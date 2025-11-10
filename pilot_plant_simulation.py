"""
Simulación específica para la planta piloto de tratamiento de agua
Adaptada a las dimensiones y condiciones reales del laboratorio
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from water_treatment_simulation import WaterTreatmentSimulation
from pilot_plant_config import *

class PilotPlantSimulation(WaterTreatmentSimulation):
    """Simulación adaptada para la planta piloto específica"""
    
    def __init__(self):
        super().__init__()
        self.pilot_specs = PILOT_PLANT_SPECS
        self.pilot_operation = PILOT_OPERATION
        self.hydraulic_params = None
        
    def setup_pilot_system(self, water_temp=20, water_pH=7.2, water_alkalinity=100, 
                          initial_turbidity=50, coagulant_dose=0.025):
        """Configurar sistema con especificaciones de la planta piloto"""
        
        # Calcular parámetros hidráulicos reales
        self.hydraulic_params = calculate_hydraulic_parameters()
        
        # Configurar con dimensiones reales
        params = {
            'temperature': water_temp,
            'pH': water_pH,
            'alkalinity': water_alkalinity,
            'turbidity': initial_turbidity,
            'initial_solids': initial_turbidity,
            
            # Usar caudal real de la planta piloto
            'flow_rate': PILOT_OPERATION['flow_rate_m3h'],
            
            # Mezcla rápida - dimensiones reales
            'rapid_mix_volume': self.pilot_specs['rapid_mix']['volume'],
            'rapid_mix_G': self.hydraulic_params['rapid_mix']['G_calculated'],
            'rapid_mix_time': PILOT_OPERATION['rapid_mix_time'],
            
            # Floculación - una cámara con bafles
            'floc_chambers': 1,
            'floc_volume': self.pilot_specs['flocculation']['volume'],
            'floc_G': self.hydraulic_params['flocculation']['G_calculated'],
            'floc_time': PILOT_OPERATION['floc_time'],
            
            # Sedimentación - dimensiones reales
            'sed_area': self.pilot_specs['sedimentation']['area'],
            'sed_height': self.pilot_specs['sedimentation']['water_height'],
            'overflow_rate': self.hydraulic_params['sedimentation']['surface_loading']
        }
        
        self.setup_system(**params)
        self.coagulant_dose = coagulant_dose
        
        print("🔧 PLANTA PILOTO CONFIGURADA")
        print("=" * 40)
        print(f"Caudal: {PILOT_OPERATION['flow_rate']:.2f} L/s")
        print(f"Volumen total: {PILOT_OPERATION['total_volume']*1000:.1f} L")
        print(f"Tiempo retención total: {PILOT_OPERATION['total_retention']:.1f} s")
        print(f"G mezcla rápida: {self.hydraulic_params['rapid_mix']['G_calculated']:.0f} s⁻¹")
        print(f"G floculación: {self.hydraulic_params['flocculation']['G_calculated']:.0f} s⁻¹")
        print(f"Tasa carga superficial: {self.hydraulic_params['sedimentation']['surface_loading']:.1f} m/h")
    
    def run_pilot_experiment(self, coagulant_dose=None):
        """Ejecutar experimento en planta piloto"""
        
        if coagulant_dose is None:
            coagulant_dose = self.coagulant_dose
        
        print(f"\n🧪 EJECUTANDO EXPERIMENTO")
        print(f"Dosis coagulante: {coagulant_dose:.3f} g/L Al2(SO4)3")
        
        # Ejecutar simulación
        results = self.run_simulation(coagulant_dose=coagulant_dose)
        
        # Añadir información específica del piloto
        results['pilot_info'] = {
            'hydraulic_params': self.hydraulic_params,
            'actual_dimensions': self.pilot_specs,
            'operating_conditions': self.pilot_operation,
            'coagulant_dose': coagulant_dose
        }
        
        # Calcular parámetros adicionales específicos del piloto
        results['pilot_performance'] = self._calculate_pilot_performance(results)
        
        return results
    
    def _calculate_pilot_performance(self, results):
        """Calcular parámetros de rendimiento específicos del piloto"""
        
        # Eficiencia por unidad
        rapid_mix_efficiency = 0  # No hay remoción en mezcla rápida
        floc_efficiency = 5       # Pequeña remoción por agregación
        sed_efficiency = results['final_efficiency'] - floc_efficiency
        
        # Consumo de coagulante
        coagulant_consumption = (self.coagulant_dose * 
                               PILOT_OPERATION['flow_rate_m3h'] * 24)  # g/día
        
        # Producción de lodos
        initial_solids = results['initial']['turbidity']  # mg/L
        final_solids = results['sedimentation']['effluent_concentration']  # mg/L
        removed_solids = initial_solids - final_solids  # mg/L
        
        sludge_production = (removed_solids * 
                           PILOT_OPERATION['flow_rate_m3h'] * 24 / 1000)  # g/día
        
        # Tiempo de retención real vs teórico
        theoretical_retention = (self.pilot_specs['rapid_mix']['volume'] + 
                               self.pilot_specs['flocculation']['volume'] + 
                               self.pilot_specs['sedimentation']['volume']) / \
                              (PILOT_OPERATION['flow_rate'] / 1000 / 3600)
        
        return {
            'efficiency_breakdown': {
                'rapid_mix': rapid_mix_efficiency,
                'flocculation': floc_efficiency,
                'sedimentation': sed_efficiency,
                'total': results['final_efficiency']
            },
            'consumption': {
                'coagulant_g_per_day': coagulant_consumption,
                'coagulant_g_per_m3': self.coagulant_dose,
                'sludge_g_per_day': sludge_production
            },
            'hydraulics': {
                'theoretical_retention_s': theoretical_retention,
                'actual_retention_s': PILOT_OPERATION['total_retention'],
                'hydraulic_efficiency': PILOT_OPERATION['total_retention'] / theoretical_retention
            }
        }
    
    def dose_response_curve(self, dose_range=None, n_points=8):
        """Generar curva de respuesta a la dosis de coagulante"""
        
        if dose_range is None:
            dose_range = [0.005, 0.060]  # g/L
        
        doses = np.linspace(dose_range[0], dose_range[1], n_points)
        results = []
        
        print(f"\n📊 GENERANDO CURVA DOSIS-RESPUESTA")
        print(f"Rango: {dose_range[0]:.3f} - {dose_range[1]:.3f} g/L")
        print(f"Puntos: {n_points}")
        
        for i, dose in enumerate(doses):
            print(f"Ensayo {i+1}/{n_points}: {dose:.3f} g/L", end=" -> ")
            
            # Ejecutar experimento
            result = self.run_pilot_experiment(coagulant_dose=dose)
            
            results.append({
                'dose_g_L': dose,
                'efficiency_%': result['final_efficiency'],
                'final_turbidity_NTU': result['sedimentation']['effluent_concentration'],
                'final_pH': result['after_coagulation']['pH'],
                'final_alkalinity': result['after_coagulation']['alkalinity'],
                'coagulant_consumption_g_day': result['pilot_performance']['consumption']['coagulant_g_per_day']
            })
            
            print(f"{result['final_efficiency']:.1f}% eficiencia")
        
        return pd.DataFrame(results)
    
    def optimize_pilot_operation(self):
        """Optimizar condiciones de operación de la planta piloto"""
        
        print(f"\n🎯 OPTIMIZANDO OPERACIÓN DE PLANTA PILOTO")
        
        # Generar curva dosis-respuesta
        dose_curve = self.dose_response_curve()
        
        # Encontrar dosis óptima (máxima eficiencia)
        optimal_idx = dose_curve['efficiency_%'].idxmax()
        optimal_dose = dose_curve.loc[optimal_idx, 'dose_g_L']
        optimal_efficiency = dose_curve.loc[optimal_idx, 'efficiency_%']
        
        # Encontrar dosis económica (eficiencia > 90% con menor dosis)
        high_eff = dose_curve[dose_curve['efficiency_%'] >= 90]
        if not high_eff.empty:
            economic_idx = high_eff['dose_g_L'].idxmin()
            economic_dose = high_eff.loc[economic_idx, 'dose_g_L']
            economic_efficiency = high_eff.loc[economic_idx, 'efficiency_%']
        else:
            economic_dose = optimal_dose
            economic_efficiency = optimal_efficiency
        
        print(f"\n📈 RESULTADOS DE OPTIMIZACIÓN:")
        print(f"Dosis óptima: {optimal_dose:.3f} g/L (Eficiencia: {optimal_efficiency:.1f}%)")
        print(f"Dosis económica: {economic_dose:.3f} g/L (Eficiencia: {economic_efficiency:.1f}%)")
        
        # Ejecutar con condiciones óptimas
        optimal_results = self.run_pilot_experiment(coagulant_dose=optimal_dose)
        
        return {
            'dose_curve': dose_curve,
            'optimal_dose': optimal_dose,
            'optimal_efficiency': optimal_efficiency,
            'economic_dose': economic_dose,
            'economic_efficiency': economic_efficiency,
            'optimal_results': optimal_results
        }
    
    def plot_pilot_results(self, results=None, optimization=None):
        """Generar gráficas específicas para la planta piloto"""
        
        if results is None and optimization is None:
            print("No hay resultados para graficar")
            return
        
        # Configurar figura
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Curva dosis-respuesta (si hay optimización)
        if optimization:
            ax1 = fig.add_subplot(gs[0, 0])
            dose_curve = optimization['dose_curve']
            
            ax1.plot(dose_curve['dose_g_L'], dose_curve['efficiency_%'], 
                    'bo-', linewidth=2, markersize=6)
            ax1.axvline(optimization['optimal_dose'], color='red', linestyle='--', 
                       label=f'Óptima: {optimization["optimal_dose"]:.3f} g/L')
            ax1.axvline(optimization['economic_dose'], color='green', linestyle='--',
                       label=f'Económica: {optimization["economic_dose"]:.3f} g/L')
            
            ax1.set_xlabel('Dosis Al2(SO4)3 (g/L)')
            ax1.set_ylabel('Eficiencia de remoción (%)')
            ax1.set_title('Curva Dosis-Respuesta')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            ax1.set_ylim(0, 100)
        
        # 2. pH vs Dosis
        if optimization:
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.plot(dose_curve['dose_g_L'], dose_curve['final_pH'], 
                    'ro-', linewidth=2, markersize=6)
            ax2.set_xlabel('Dosis Al2(SO4)3 (g/L)')
            ax2.set_ylabel('pH final')
            ax2.set_title('Efecto en pH')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(6, 8)
        
        # 3. Alcalinidad vs Dosis
        if optimization:
            ax3 = fig.add_subplot(gs[0, 2])
            ax3.plot(dose_curve['dose_g_L'], dose_curve['final_alkalinity'], 
                    'go-', linewidth=2, markersize=6)
            ax3.set_xlabel('Dosis Al2(SO4)3 (g/L)')
            ax3.set_ylabel('Alcalinidad final (mg/L CaCO3)')
            ax3.set_title('Consumo de Alcalinidad')
            ax3.grid(True, alpha=0.3)
        
        # 4. Esquema de la planta piloto
        ax4 = fig.add_subplot(gs[1, :])
        self._draw_pilot_plant_scheme(ax4)
        
        # 5. Distribución de tamaños (si hay resultados individuales)
        if results:
            ax5 = fig.add_subplot(gs[2, 0])
            ax5.semilogx(self.particles.sizes, self.particles.concentrations, 
                        'b-', linewidth=2, label='Inicial')
            
            if 'flocculation' in results:
                final_chamber = results['flocculation'][-1]
                final_dist = final_chamber['distribution'][:, -1]
                ax5.semilogx(self.particles.sizes, final_dist, 
                           'r-', linewidth=2, label='Post-floculación')
            
            ax5.semilogx(self.particles.sizes, 
                        results['sedimentation']['size_distribution'], 
                        'g-', linewidth=2, label='Efluente')
            
            ax5.set_xlabel('Tamaño de partícula (μm)')
            ax5.set_ylabel('Concentración (mg/L)')
            ax5.set_title('Distribución de Tamaños')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # 6. Balance de masa por unidad
        if results:
            ax6 = fig.add_subplot(gs[2, 1])
            
            stages = ['Entrada', 'Mezcla\nRápida', 'Floculación', 'Sedimentación']
            concentrations = [
                results['initial']['turbidity'],
                results['initial']['turbidity'],  # Sin cambio en mezcla rápida
                results['initial']['turbidity'] * 0.95,  # Pequeña reducción en floc
                results['sedimentation']['effluent_concentration']
            ]
            
            colors = ['blue', 'orange', 'green', 'red']
            bars = ax6.bar(stages, concentrations, color=colors, alpha=0.7)
            
            # Añadir valores
            for bar, conc in zip(bars, concentrations):
                height = bar.get_height()
                ax6.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{conc:.1f}', ha='center', va='bottom', fontweight='bold')
            
            ax6.set_ylabel('Concentración (mg/L)')
            ax6.set_title('Balance de Masa por Etapa')
            ax6.tick_params(axis='x', rotation=45)
        
        # 7. Parámetros hidráulicos
        if results and 'pilot_info' in results:
            ax7 = fig.add_subplot(gs[2, 2])
            
            hydraulic = results['pilot_info']['hydraulic_params']
            
            params_text = f"""
PARÁMETROS HIDRÁULICOS CALCULADOS

Mezcla Rápida:
• Velocidad chorro: {hydraulic['rapid_mix']['jet_velocity']:.1f} m/s
• Gradiente G: {hydraulic['rapid_mix']['G_calculated']:.0f} s⁻¹
• Potencia: {hydraulic['rapid_mix']['power_dissipated']:.3f} W

Floculación:
• Velocidad bafles: {hydraulic['flocculation']['baffle_velocity']:.3f} m/s
• Gradiente G: {hydraulic['flocculation']['G_calculated']:.0f} s⁻¹
• Pérdida carga: {hydraulic['flocculation']['head_loss']:.4f} m

Sedimentación:
• Velocidad ascensional: {hydraulic['sedimentation']['upflow_velocity']*1000:.2f} mm/s
• Velocidad orificios: {hydraulic['sedimentation']['hole_velocity']:.3f} m/s
• Carga superficial: {hydraulic['sedimentation']['surface_loading']:.1f} m/h

RENDIMIENTO:
• Eficiencia total: {results['final_efficiency']:.1f}%
• Turbidez final: {results['sedimentation']['effluent_concentration']:.1f} mg/L
• pH final: {results['after_coagulation']['pH']:.2f}
            """
            
            ax7.text(0.05, 0.95, params_text, transform=ax7.transAxes, 
                    fontsize=9, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            ax7.axis('off')
        
        plt.suptitle('RESULTADOS PLANTA PILOTO DE TRATAMIENTO DE AGUA', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()
    
    def _draw_pilot_plant_scheme(self, ax):
        """Dibujar esquema de la planta piloto"""
        
        # Dimensiones para el dibujo (escaladas)
        box_width = 3
        box_height = 2
        spacing = 1
        
        # Caja 1 - Mezcla Rápida
        rect1 = plt.Rectangle((0, 0), box_width, box_height, 
                             fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(rect1)
        ax.text(box_width/2, box_height/2, 'MEZCLA\nRÁPIDA\n15.4 L\nG≈825 s⁻¹', 
               ha='center', va='center', fontweight='bold', fontsize=10)
        
        # Deflector
        ax.plot([box_width*0.7, box_width*0.7], [box_height*0.3, box_height*0.7], 
               'r-', linewidth=3, label='Deflector')
        
        # Caja 2 - Floculación
        rect2 = plt.Rectangle((box_width + spacing, 0), box_width, box_height, 
                             fill=False, edgecolor='green', linewidth=2)
        ax.add_patch(rect2)
        ax.text(box_width + spacing + box_width/2, box_height/2, 
               'FLOCULACIÓN\n15.4 L\n7 bafles\nG≈40 s⁻¹', 
               ha='center', va='center', fontweight='bold', fontsize=10)
        
        # Bafles
        for i in range(3):
            x_baffle = box_width + spacing + 0.5 + i*0.8
            if i % 2 == 0:
                ax.plot([x_baffle, x_baffle], [0.2, box_height*0.8], 'g-', linewidth=2)
            else:
                ax.plot([x_baffle, x_baffle], [box_height*0.2, box_height-0.2], 'g-', linewidth=2)
        
        # Caja 3 - Sedimentación
        rect3 = plt.Rectangle((2*(box_width + spacing), 0), box_width*0.6, box_height, 
                             fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(rect3)
        ax.text(2*(box_width + spacing) + box_width*0.3, box_height/2, 
               'SEDIMEN-\nTACIÓN\n6.7 L\n55 orificios', 
               ha='center', va='center', fontweight='bold', fontsize=9)
        
        # Piso falso
        ax.plot([2*(box_width + spacing) + 0.1, 2*(box_width + spacing) + box_width*0.6 - 0.1], 
               [0.3, 0.3], 'r--', linewidth=2, label='Piso falso')
        
        # Flechas de flujo
        arrow_props = dict(arrowstyle='->', lw=2, color='black')
        
        # Entrada
        ax.annotate('', xy=(0, box_height/2), xytext=(-0.5, box_height/2), 
                   arrowprops=arrow_props)
        ax.text(-0.7, box_height/2 + 0.3, 'Q=0.45 L/s', ha='center', fontsize=9)
        
        # Entre cajas
        ax.annotate('', xy=(box_width + spacing, box_height/2), 
                   xytext=(box_width, box_height/2), arrowprops=arrow_props)
        
        ax.annotate('', xy=(2*(box_width + spacing), box_height/2), 
                   xytext=(box_width + spacing + box_width, box_height/2), 
                   arrowprops=arrow_props)
        
        # Salida
        ax.annotate('', xy=(2*(box_width + spacing) + box_width*0.6 + 0.5, box_height/2), 
                   xytext=(2*(box_width + spacing) + box_width*0.6, box_height/2), 
                   arrowprops=arrow_props)
        ax.text(2*(box_width + spacing) + box_width*0.6 + 0.7, box_height/2 + 0.3, 
               'Efluente', ha='center', fontsize=9)
        
        # Configurar ejes
        ax.set_xlim(-1, 2*(box_width + spacing) + box_width*0.6 + 1)
        ax.set_ylim(-0.5, box_height + 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('ESQUEMA DE LA PLANTA PILOTO', fontweight='bold', fontsize=12)

def run_pilot_plant_analysis():
    """Ejecutar análisis completo de la planta piloto"""
    
    print("🏭 ANÁLISIS COMPLETO DE PLANTA PILOTO")
    print("=" * 50)
    
    # Validar diseño hidráulico
    validate_pilot_design()
    
    # Crear simulación
    pilot = PilotPlantSimulation()
    
    # Configurar con condiciones típicas
    pilot.setup_pilot_system(
        water_temp=20,
        water_pH=7.2,
        water_alkalinity=100,
        initial_turbidity=50,
        coagulant_dose=0.025
    )
    
    # Ejecutar experimento base
    print(f"\n🧪 EXPERIMENTO BASE")
    base_results = pilot.run_pilot_experiment()
    
    # Optimización
    print(f"\n🎯 OPTIMIZACIÓN")
    optimization = pilot.optimize_pilot_operation()
    
    # Generar gráficas
    pilot.plot_pilot_results(results=base_results, optimization=optimization)
    
    # Escalamiento a planta real
    scaled = scale_to_full_plant(base_results)
    
    print(f"\n📏 ESCALAMIENTO A PLANTA REAL:")
    print(f"Caudal planta real: {scaled['flow_rate_full']:.0f} m³/h")
    print(f"Volumen total: {scaled['volume_full']:.0f} m³")
    print(f"Área sedimentador: {scaled['area_full']:.0f} m²")
    print(f"Tiempo retención: {scaled['time_full']/60:.0f} min")
    
    return pilot, base_results, optimization

if __name__ == "__main__":
    pilot_sim, results, opt = run_pilot_plant_analysis()