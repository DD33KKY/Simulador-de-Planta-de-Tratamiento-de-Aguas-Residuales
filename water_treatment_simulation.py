"""de agua con coagulante
Proceso: Mezcla rápida -> Floculación -> Sedimentación
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Intentar importar librerías especializadas (con fallbacks)
try:
    from thermo import Chemical, Mixture
    from chemicals import viscosity_liquid, density_liquid
    HAS_THERMO = True
except ImportError:
    HAS_THERMO = False
    print("Warning: thermo/chemicals not available. Using simplified models.")

try:
    import pyEQL
    HAS_PYEQL = True
except ImportError:
    HAS_PYEQL = False
    print("Warning: pyEQL not available. Using simplified pH model.")

class WaterProperties:
    """Propiedades físico-químicas del agua"""
    
    def __init__(self, temperature=20, pH=7.0, alkalinity=100, turbidity=50):
        self.temperature = temperature  # °C
        self.pH = pH
        self.alkalinity = alkalinity  # mg/L CaCO3
        self.turbidity = turbidity  # NTU
        self.update_properties()
    
    def update_properties(self):
        """Actualizar propiedades dependientes de temperatura"""
        T_K = self.temperature + 273.15
        
        if HAS_THERMO:
            water = Chemical('water', T=T_K)
            self.density = water.rho  # kg/m³
            self.viscosity = water.mu  # Pa·s
        else:
            # Correlaciones simplificadas para densidad y viscosidad del agua
            # Densidad: correlación empírica (aproximada)
            # A 4°C: 1000 kg/m³, disminuye ligeramente con temperatura
            self.density = 1000 - 0.0178 * (self.temperature - 4)**1.9  # kg/m³
            
            # Viscosidad: correlación empírica para agua
            # μ(20°C) = 1.002 mPa·s = 0.001002 Pa·s
            # Fórmula simplificada: μ(T) = 0.001792 * exp(-1.94 - 4.80/(T+273.15))
            # O más simple y precisa: μ(T) = 0.001792 * exp(-0.0337 * T) para T en °C
            # Validación: a 20°C debería dar ~0.001002 Pa·s
            # Usamos fórmula de Vogel-Fulcher-Tammann simplificada
            T_K = self.temperature + 273.15
            # Fórmula estándar: μ = A * 10^(B/(T-C)) donde A=2.414e-5, B=247.8, C=140
            # Simplificada para rango 0-40°C:
            self.viscosity = 2.414e-5 * (10**(247.8 / (T_K - 140)))  # Pa·s
    
    def add_coagulant(self, al2so4_conc, volume):
        """Simular adición de sulfato de aluminio
        
        Args:
            al2so4_conc: Concentración de Al2(SO4)3 en g/L
            volume: Volumen del tanque en m³ (no usado actualmente, pero puede ser útil)
        
        Reacción: Al2(SO4)3 + 6H2O -> 2Al(OH)3 + 3H2SO4
        Consumo de alcalinidad: 1 mol Al2(SO4)3 consume 6 mol CaCO3 (equivalente)
        """
        # Peso molecular Al2(SO4)3 = 342.15 g/mol
        # Peso molecular CaCO3 = 100.09 g/mol
        molar_conc = al2so4_conc / 342.15  # mol/L
        
        # Consumo de alcalinidad: 1 mol Al2(SO4)3 consume 6 mol CaCO3
        # molar_conc está en mol/L, entonces:
        # moles CaCO3 consumidos = molar_conc * 6 (mol/L)
        # masa CaCO3 consumida = molar_conc * 6 * 100.09 (g/L)
        # convertir a mg/L: * 1000
        alkalinity_consumed = molar_conc * 6 * 100.09 * 1000  # mg/L CaCO3
        
        self.alkalinity = max(0, self.alkalinity - alkalinity_consumed)
        
        # Cambio de pH basado en consumo de alcalinidad
        # Modelo simplificado: pH disminuye cuando se consume alcalinidad
        if HAS_PYEQL:
            # Usar pyEQL para cálculo exacto si está disponible
            pass  # Implementar si está disponible
        else:
            # Modelo simplificado basado en relación alcalinidad-pH
            # Aproximación: cada 50 mg/L de alcalinidad consumida reduce pH en ~0.1-0.2 unidades
            # (depende del sistema buffer, pero es una aproximación razonable)
            if alkalinity_consumed > 0:
                # Factor de amortiguación: el agua tiene capacidad buffer
                buffer_capacity = 0.15  # unidades pH por cada 100 mg/L CaCO3 consumido
                delta_pH = -(alkalinity_consumed / 100.0) * buffer_capacity
                self.pH = max(4.0, min(9.0, self.pH + delta_pH))
        
        return self.pH, self.alkalinity

class ParticleDistribution:
    """Distribución de tamaño de partículas"""
    
    def __init__(self, sizes=None, concentrations=None):
        if sizes is None:
            # Distribución log-normal típica para arcilla
            self.sizes = np.logspace(-1, 2, 50)  # 0.1 a 100 μm
            self.concentrations = self._lognormal_distribution(self.sizes, 2.0, 0.8)
        else:
            self.sizes = np.array(sizes)
            self.concentrations = np.array(concentrations)
    
    def _lognormal_distribution(self, x, mu, sigma):
        """Distribución log-normal"""
        return np.exp(-(np.log(x) - mu)**2 / (2 * sigma**2)) / (x * sigma * np.sqrt(2 * np.pi))
    
    def normalize(self, total_concentration):
        """Normalizar a concentración total específica"""
        current_total = np.trapz(self.concentrations, self.sizes)
        self.concentrations = self.concentrations * total_concentration / current_total
    
    def mean_size(self):
        """Tamaño medio ponderado por masa"""
        return np.trapz(self.sizes * self.concentrations, self.sizes) / np.trapz(self.concentrations, self.sizes)

class RapidMixing:
    """Etapa de mezcla rápida (coagulación)"""
    
    def __init__(self, volume=10, flow_rate=100, G=1000, mixing_time=30):
        self.volume = volume  # m³
        self.flow_rate = flow_rate  # m³/h
        self.G = G  # s⁻¹ (gradiente de velocidad)
        self.mixing_time = mixing_time  # s
        self.residence_time = volume / (flow_rate / 3600)  # s
    
    def process(self, water_props, particles, coagulant_dose):
        """Procesar mezcla rápida"""
        # Añadir coagulante
        new_pH, new_alkalinity = water_props.add_coagulant(coagulant_dose, self.volume)
        
        # Desestabilización de partículas (modelo simplificado)
        # Incremento en eficiencia de colisión debido a neutralización de cargas
        charge_neutralization = min(1.0, coagulant_dose / 0.05)  # Saturación a 0.05 g/L
        
        # Modificar distribución inicial (agregación primaria)
        new_particles = ParticleDistribution()
        new_particles.sizes = particles.sizes * (1 + 0.1 * charge_neutralization)
        new_particles.concentrations = particles.concentrations
        new_particles.normalize(np.trapz(particles.concentrations, particles.sizes))
        
        return water_props, new_particles

class Flocculation:
    """Etapa de floculación con Population Balance Model"""
    
    def __init__(self, chambers=3, total_volume=200, G_avg=50, total_time=1800):
        self.chambers = chambers
        self.total_volume = total_volume  # m³
        self.G_avg = G_avg  # s⁻¹
        self.total_time = total_time  # s
        self.chamber_volume = total_volume / chambers
        self.chamber_time = total_time / chambers
    
    def coagulation_kernel(self, di, dj, G, temperature, viscosity):
        """Kernel de coagulación (Smoluchowski + turbulento)
        
        Fórmula de Smoluchowski para coagulación browniana:
        K_brown = (2*kB*T)/(3*μ) * (di + dj)²/(di*dj)
        
        Fórmula para coagulación turbulenta (Saffman-Turner):
        K_turb = α * (ε/ν)^(1/2) * (di + dj)³
        donde ε = G²*μ/ρ es la disipación de energía
        """
        # Constantes
        kB = 1.38e-23  # J/K (constante de Boltzmann)
        T = temperature + 273.15  # K
        rho = 1000  # kg/m³ (densidad del agua, aproximada)
        
        # Coagulación Browniana (Smoluchowski)
        # K_brown = (2*kB*T)/(3*μ) * (di + dj)²/(di*dj)
        K_brown = (2 * kB * T) / (3 * viscosity) * ((di + dj)**2) / (di * dj)
        
        # Coagulación Turbulenta (Saffman-Turner modificado)
        # Disipación de energía: ε = G² * μ / ρ
        epsilon = (G**2 * viscosity) / rho  # m²/s³
        
        # Tasa de deformación: (ε/ν)^(1/2) donde ν = μ/ρ es la viscosidad cinemática
        nu = viscosity / rho  # m²/s (viscosidad cinemática)
        shear_rate = np.sqrt(epsilon / nu)  # s⁻¹
        
        # Kernel turbulento: α * shear_rate * (di + dj)³
        # α es un factor de eficiencia de colisión (típicamente 0.1-0.3)
        alpha = 0.2  # Factor de eficiencia de colisión
        K_turb = alpha * shear_rate * (di + dj)**3
        
        return K_brown + K_turb
    
    def breakage_kernel(self, d, G, density_floc=1050, viscosity=1e-3, density_water=1000):
        """Kernel de rotura por esfuerzo turbulento
        
        Modelo basado en esfuerzo cortante turbulento:
        S(d) = C_break * (ε/ν)^(1/2) * d^(2/3)
        
        donde:
        - ε = G² * μ / ρ es la disipación de energía (m²/s³)
        - ν = μ / ρ es la viscosidad cinemática (m²/s)
        - d es el diámetro de la partícula (m)
        """
        # Disipación de energía: ε = G² * μ / ρ
        epsilon = (G**2 * viscosity) / density_water  # m²/s³
        
        # Viscosidad cinemática
        nu = viscosity / density_water  # m²/s
        
        # Tasa de rotura: S(d) = C_break * (ε/ν)^(1/2) * d^(2/3)
        # C_break es una constante empírica (típicamente 1e-6 a 1e-4)
        C_break = 1e-5  # Constante de calibración (ajustada para mejor realismo)
        
        # Tasa de deformación turbulenta
        shear_rate = np.sqrt(epsilon / nu)  # s⁻¹
        
        # Kernel de rotura
        S = C_break * shear_rate * (d**(2/3))
        
        return S
    
    def population_balance(self, t, n, sizes, G, water_props):
        """Ecuación de balance poblacional"""
        N = len(sizes)
        dndt = np.zeros(N)
        
        for i in range(N):
            # Término de agregación (ganancia)
            birth = 0
            for j in range(i):
                if j < N and i-j-1 < N:
                    K_ij = self.coagulation_kernel(
                        sizes[j]*1e-6, sizes[i-j-1]*1e-6, G, 
                        water_props.temperature, water_props.viscosity
                    )
                    birth += 0.5 * K_ij * n[j] * n[i-j-1]
            
            # Término de agregación (pérdida)
            death_agg = 0
            for j in range(N):
                K_ij = self.coagulation_kernel(
                    sizes[i]*1e-6, sizes[j]*1e-6, G,
                    water_props.temperature, water_props.viscosity
                )
                death_agg += K_ij * n[i] * n[j]
            
            # Término de rotura
            S_i = self.breakage_kernel(sizes[i]*1e-6, G,
                                      density_floc=1200,
                                      viscosity=water_props.viscosity,
                                      density_water=water_props.density)
            death_break = S_i * n[i]
            
            # Ganancia por rotura de partículas más grandes
            birth_break = 0
            for j in range(i+1, N):
                S_j = self.breakage_kernel(sizes[j]*1e-6, G,
                                          density_floc=1200,
                                          viscosity=water_props.viscosity,
                                          density_water=water_props.density)
                # Función de distribución de fragmentos (simplificada)
                # Cuando una partícula de tamaño j se rompe, produce fragmentos de tamaño i
                # Modelo simplificado: distribución uniforme de fragmentos
                b_ij = 2.0 / (j - i + 1) if j > i else 0.0  # Normalizado
                birth_break += b_ij * S_j * n[j]
            
            dndt[i] = birth - death_agg - death_break + birth_break
        
        return dndt
    
    def process(self, water_props, particles):
        """Procesar floculación"""
        results = []
        current_particles = particles
        
        for chamber in range(self.chambers):
            # Resolver balance poblacional para esta cámara
            t_span = [0, self.chamber_time]
            t_eval = np.linspace(0, self.chamber_time, 100)
            
            sol = solve_ivp(
                lambda t, n: self.population_balance(t, n, current_particles.sizes, 
                                                   self.G_avg, water_props),
                t_span, current_particles.concentrations,
                t_eval=t_eval, method='RK45', rtol=1e-6
            )
            
            # Actualizar distribución
            current_particles.concentrations = sol.y[:, -1]
            
            # Guardar resultados
            results.append({
                'chamber': chamber + 1,
                'time': t_eval,
                'distribution': sol.y,
                'mean_size': [np.trapz(current_particles.sizes * dist, current_particles.sizes) / 
                             np.trapz(dist, current_particles.sizes) for dist in sol.y.T]
            })
        
        return current_particles, results

class Sedimentation:
    """Etapa de sedimentación"""
    
    def __init__(self, area=100, height=3, overflow_rate=10):
        self.area = area  # m²
        self.height = height  # m
        self.overflow_rate = overflow_rate  # m³/m²/h
        self.residence_time = height / (overflow_rate / 3600)  # s
    
    def settling_velocity(self, diameter, density_particle, water_props):
        """Velocidad de sedimentación (Ley de Stokes modificada)"""
        d = diameter * 1e-6  # m
        rho_p = density_particle  # kg/m³
        rho_w = water_props.density
        mu = water_props.viscosity
        g = 9.81
        
        # Número de Reynolds
        vs_stokes = g * d**2 * (rho_p - rho_w) / (18 * mu)
        Re = rho_w * vs_stokes * d / mu
        
        # Corrección para Re > 0.1
        if Re > 0.1:
            Cd = 24/Re + 3/np.sqrt(Re) + 0.34  # Correlación de Schiller-Naumann
            vs = np.sqrt(4 * g * d * (rho_p - rho_w) / (3 * Cd * rho_w))
        else:
            vs = vs_stokes
        
        return vs
    
    def hindered_settling(self, vs0, concentration, density_particle=1200, n=4.65):
        """Sedimentación obstaculizada (Richardson-Zaki)
        
        vs_hindered = vs0 * (1 - φ)^n
        
        donde:
        - vs0: velocidad de sedimentación libre (m/s)
        - φ: fracción volumétrica de sólidos
        - n: exponente (típicamente 4.65 para partículas esféricas)
        
        Args:
            vs0: velocidad de sedimentación libre (m/s)
            concentration: concentración de sólidos en mg/L
            density_particle: densidad de las partículas en kg/m³
            n: exponente de Richardson-Zaki
        """
        # Convertir concentración de mg/L a fracción volumétrica
        # concentration está en mg/L = g/m³
        # densidad de partículas está en kg/m³ = g/L
        # fracción volumétrica φ = (concentración en g/m³) / (densidad en g/m³)
        # φ = (concentration / 1000) / (density_particle * 1000) = concentration / (density_particle * 1e6)
        # Pero más simple: si concentration está en mg/L y density_particle en kg/m³:
        # φ = (concentration / 1e6) / (density_particle / 1000) = concentration / (density_particle * 1000)
        
        # Conversión correcta: mg/L -> kg/m³ -> fracción volumétrica
        conc_kg_m3 = concentration / 1e6  # convertir mg/L a kg/m³
        phi = conc_kg_m3 / density_particle  # fracción volumétrica (adimensional)
        
        # Limitar phi a valores físicamente razonables (0-0.6)
        phi = min(0.6, max(0.0, phi))
        
        return vs0 * (1 - phi)**n
    
    def process(self, water_props, particles, floc_density=1200):
        """Procesar sedimentación"""
        # Calcular velocidades de sedimentación para cada tamaño
        settling_velocities = np.array([
            self.settling_velocity(d, floc_density, water_props) 
            for d in particles.sizes
        ])
        
        # Concentración total
        total_conc = np.trapz(particles.concentrations, particles.sizes)
        
        # Aplicar sedimentación obstaculizada
        vs_hindered = np.array([
            self.hindered_settling(vs, total_conc, floc_density) 
            for vs in settling_velocities
        ])
        
        # Eficiencia de remoción por tamaño
        removal_efficiency = np.minimum(1.0, vs_hindered * self.residence_time / self.height)
        
        # Concentración en el efluente
        effluent_conc = particles.concentrations * (1 - removal_efficiency)
        
        # Concentración total removida
        initial_total = np.trapz(particles.concentrations, particles.sizes)
        final_total = np.trapz(effluent_conc, particles.sizes)
        overall_efficiency = (initial_total - final_total) / initial_total * 100
        
        return {
            'effluent_concentration': final_total,
            'removal_efficiency': overall_efficiency,
            'size_distribution': effluent_conc,
            'settling_velocities': vs_hindered
        }

class WaterTreatmentSimulation:
    """Simulación completa del tren de tratamiento"""
    
    def __init__(self):
        self.water_props = None
        self.particles = None
        self.rapid_mix = None
        self.flocculation = None
        self.sedimentation = None
        self.results = {}
    
    def setup_system(self, **kwargs):
        """Configurar el sistema con parámetros"""
        # Propiedades del agua
        self.water_props = WaterProperties(
            temperature=kwargs.get('temperature', 20),
            pH=kwargs.get('pH', 7.0),
            alkalinity=kwargs.get('alkalinity', 100),
            turbidity=kwargs.get('turbidity', 50)
        )
        
        # Distribución inicial de partículas
        self.particles = ParticleDistribution()
        self.particles.normalize(kwargs.get('initial_solids', 50))  # mg/L
        
        # Configurar etapas
        self.rapid_mix = RapidMixing(
            volume=kwargs.get('rapid_mix_volume', 10),
            flow_rate=kwargs.get('flow_rate', 100),
            G=kwargs.get('rapid_mix_G', 1000),
            mixing_time=kwargs.get('rapid_mix_time', 30)
        )
        
        self.flocculation = Flocculation(
            chambers=kwargs.get('floc_chambers', 3),
            total_volume=kwargs.get('floc_volume', 200),
            G_avg=kwargs.get('floc_G', 50),
            total_time=kwargs.get('floc_time', 1800)
        )
        
        self.sedimentation = Sedimentation(
            area=kwargs.get('sed_area', 100),
            height=kwargs.get('sed_height', 3),
            overflow_rate=kwargs.get('overflow_rate', 10)
        )
    
    def run_simulation(self, coagulant_dose=0.02):
        """Ejecutar simulación completa"""
        print("Iniciando simulación de tratamiento de agua...")
        
        # Etapa 1: Mezcla rápida
        print("1. Procesando mezcla rápida...")
        water_after_mix, particles_after_mix = self.rapid_mix.process(
            self.water_props, self.particles, coagulant_dose
        )
        
        # Etapa 2: Floculación
        print("2. Procesando floculación...")
        particles_after_floc, floc_results = self.flocculation.process(
            water_after_mix, particles_after_mix
        )
        
        # Etapa 3: Sedimentación
        print("3. Procesando sedimentación...")
        sed_results = self.sedimentation.process(
            water_after_mix, particles_after_floc
        )
        
        # Compilar resultados
        self.results = {
            'initial': {
                'pH': self.water_props.pH,
                'alkalinity': self.water_props.alkalinity,
                'turbidity': self.water_props.turbidity,
                'mean_particle_size': self.particles.mean_size()
            },
            'after_coagulation': {
                'pH': water_after_mix.pH,
                'alkalinity': water_after_mix.alkalinity,
                'mean_particle_size': particles_after_mix.mean_size()
            },
            'flocculation': floc_results,
            'sedimentation': sed_results,
            'final_efficiency': sed_results['removal_efficiency']
        }
        
        print(f"Simulación completada. Eficiencia total: {sed_results['removal_efficiency']:.1f}%")
        return self.results
    
    def plot_results(self):
        """"Generar gráficas de resultados"""
        if not self.results:
            print("No hay resultados para graficar. Ejecute la simulación primero.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Gráfica 1: Evolución del tamaño medio durante floculación
        ax1 = axes[0, 0]
        for i, chamber_data in enumerate(self.results['flocculation']):
            ax1.plot(chamber_data['time']/60, chamber_data['mean_size'], 
                    label=f'Cámara {chamber_data["chamber"]}')
        ax1.set_xlabel('Tiempo (min)')
        ax1.set_ylabel('Tamaño medio (μm)')
        ax1.set_title('Evolución del tamaño de flóculos')
        ax1.legend()
        ax1.grid(True)
        
        # Gráfica 2: Distribución de tamaños final
        ax2 = axes[0, 1]
        ax2.semilogx(self.particles.sizes, self.particles.concentrations, 
                     'b-', label='Inicial')
        final_chamber = self.results['flocculation'][-1]
        final_dist = final_chamber['distribution'][:, -1]
        ax2.semilogx(self.particles.sizes, final_dist, 'r-', label='Después floculación')
        ax2.semilogx(self.particles.sizes, self.results['sedimentation']['size_distribution'], 
                     'g-', label='Efluente')
        ax2.set_xlabel('Tamaño de partícula (μm)')
        ax2.set_ylabel('Concentración (mg/L)')
        ax2.set_title('Distribución de tamaños')
        ax2.legend()
        ax2.grid(True)
        
        # Gráfica 3: Velocidades de sedimentación
        ax3 = axes[1, 0]
        ax3.loglog(self.particles.sizes, self.results['sedimentation']['settling_velocities']*1000)
        ax3.set_xlabel('Tamaño de partícula (μm)')
        ax3.set_ylabel('Velocidad de sedimentación (mm/s)')
        ax3.set_title('Velocidades de sedimentación')
        ax3.grid(True)
        
        # Gráfica 4: Resumen de eficiencias
        ax4 = axes[1, 1]
        stages = ['Inicial', 'Coagulación', 'Floculación', 'Sedimentación']
        concentrations = [
            self.results['initial']['turbidity'],
            self.results['initial']['turbidity'],  # Sin cambio en coagulación
            np.trapz(self.results['flocculation'][-1]['distribution'][:, -1], self.particles.sizes),
            self.results['sedimentation']['effluent_concentration']
        ]
        ax4.bar(stages, concentrations, color=['blue', 'orange', 'green', 'red'])
        ax4.set_ylabel('Concentración de sólidos (mg/L)')
        ax4.set_title('Concentración por etapa')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
        
        # Imprimir resumen
        print("\n" + "="*50)
        print("RESUMEN DE RESULTADOS")
        print("="*50)
        print(f"pH inicial: {self.results['initial']['pH']:.2f}")
        print(f"pH final: {self.results['after_coagulation']['pH']:.2f}")
        print(f"Alcalinidad inicial: {self.results['initial']['alkalinity']:.1f} mg/L CaCO3")
        print(f"Alcalinidad final: {self.results['after_coagulation']['alkalinity']:.1f} mg/L CaCO3")
        print(f"Tamaño medio inicial: {self.results['initial']['mean_particle_size']:.2f} μm")
        print(f"Tamaño medio después coagulación: {self.results['after_coagulation']['mean_particle_size']:.2f} μm")
        print(f"Concentración inicial: {self.results['initial']['turbidity']:.1f} mg/L")
        print(f"Concentración final: {self.results['sedimentation']['effluent_concentration']:.1f} mg/L")
        print(f"EFICIENCIA TOTAL DE REMOCIÓN: {self.results['final_efficiency']:.1f}%")

if __name__ == "__main__":
    # Ejemplo de uso
    sim = WaterTreatmentSimulation()
    
    # Configurar parámetros del sistema
    params = {
        'temperature': 20,  # °C
        'pH': 7.5,
        'alkalinity': 120,  # mg/L CaCO₃
        'turbidity': 50,  # NTU
        'initial_solids': 50,  # mg/L
        'flow_rate': 100,  # m³/h
        'rapid_mix_volume': 10,  # m³
        'rapid_mix_G': 1000,  # s⁻¹
        'rapid_mix_time': 30,  # s
        'floc_chambers': 3,
        'floc_volume': 200,  # m³
        'floc_G': 50,  # s⁻¹
        'floc_time': 1800,  # s (30 min)
        'sed_area': 100,  # m²
        'sed_height': 3,  # m
        'overflow_rate': 10  # m³/m²/h
    }
    
    sim.setup_system(**params)
    
    # Ejecutar simulación con dosis de coagulante
    results = sim.run_simulation(coagulant_dose=0.02)  # g/L
    
    # Generar gráficas
    sim.plot_results()