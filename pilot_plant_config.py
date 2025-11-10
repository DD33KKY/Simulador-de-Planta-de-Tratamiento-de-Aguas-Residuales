"""
Configuración específica para la planta piloto de tratamiento de agua
Basada en las especificaciones técnicas del sistema de laboratorio
"""

import numpy as np

# =============================================================================
# ESPECIFICACIONES DE LA PLANTA PILOTO
# =============================================================================

# Dimensiones reales del sistema (en metros para cálculos)
PILOT_PLANT_SPECS = {
    # Caja 1 - Mezcla Rápida Hidráulica
    'rapid_mix': {
        'length': 0.315,        # m (31.5 cm)
        'width': 0.315,         # m (31.5 cm)
        'total_height': 0.165,  # m (16.5 cm)
        'water_height': 0.155,  # m (15.5 cm)
        'volume': 0.0154,       # m³ (15.4 L)
        'flow_rate_range': [0.40, 0.50],  # L/s
        'mixing_time': [3, 4],  # s
        'G_range': [750, 900],  # s⁻¹
        
        # Elementos constructivos
        'baffle_size': [0.08, 0.08],      # m (8x8 cm deflector)
        'baffle_distance': 0.02,          # m (2 cm del chorro)
        'inlet_diameter': [0.020, 0.022], # m (20-22 mm orificio)
        'outlet_height': 0.03,            # m (3 cm ranura)
        'outlet_bottom': 0.125,           # m (12.5 cm del fondo)
        'chamber_separation': 0.03        # m (3 cm tabique)
    },
    
    # Caja 2 - Floculador Hidráulico
    'flocculation': {
        'length': 0.315,        # m (31.5 cm)
        'width': 0.315,         # m (31.5 cm)
        'total_height': 0.165,  # m (16.5 cm)
        'water_height': 0.155,  # m (15.5 cm)
        'volume': 0.0154,       # m³ (15.4 L)
        'retention_time': [10, 20],  # min (a escala)
        'G_range': [20, 60],    # s⁻¹
        
        # Configuración de bafles
        'n_baffles': 7,
        'baffle_thickness': 0.003,     # m (3 mm acrílico)
        'baffle_separation': 0.033,    # m (3.3 cm)
        'baffle_width': 0.312,         # m (31.2 cm)
        'step_total': 0.036,           # m (3.6 cm paso total)
        'opening_free': 0.044,         # m (4.4 cm abertura libre)
        
        # Alturas alternadas
        'lower_step': 0.101,           # m (10.1 cm)
        'upper_step': 0.111,           # m (11.1 cm)
        'lower_clearance': 0.008,      # m (0.8 cm)
        'upper_clearance': 0.010,      # m (1.0 cm)
        
        # Distribución de láminas
        'upper_baffles': 4,            # láminas paso superior
        'lower_baffles': 3             # láminas paso inferior
    },
    
    # Caja 3 - Sedimentador Vertical
    'sedimentation': {
        'length': 0.29,         # m (29 cm)
        'width': 0.15,          # m (15 cm)
        'total_height': 0.165,  # m (16.5 cm)
        'water_height': 0.155,  # m (15.5 cm)
        'volume': 0.0067,       # m³ (6.7 L)
        'area': 0.0435,         # m² (29x15 cm)
        'flow_rate_range': [0.60, 0.70],  # L/min
        'SOR_range': [0.8, 1.0],          # m/h (tasa carga superficial)
        'detention_time': [10, 12],       # min
        
        # Piso falso
        'false_floor': {
            'height': 0.01,             # m (1 cm sobre fondo)
            'thickness': 0.003,         # m (3 mm acrílico)
            'plate_length': 0.288,      # m (28.8 cm)
            'plate_width': 0.148,       # m (14.8 cm)
            'support_height': 0.01,     # m (1 cm listones)
            
            # Orificios
            'hole_diameter': 0.002,     # m (2 mm)
            'hole_spacing': 0.025,      # m (2.5 cm entre centros)
            'margin': 0.015,            # m (1.5 cm margen)
            'total_holes': 55,
            'velocity_range': [0.06, 0.07]  # m/s en orificios
        },
        
        # Recolección superior
        'collection': {
            'n_tubes': 3,               # tubos verticales
            'tube_diameter': 0.0127,    # m (1/2" PVC)
            'overflow_height': 0.150,   # m (15 cm nivel agua)
            'hole_diameter': 0.003,     # m (3 mm perforaciones)
            'holes_per_tube': 8,
            'collector_diameter': 0.019  # m (3/4" PVC)
        }
    }
}

# =============================================================================
# PARÁMETROS OPERATIVOS DE LA PLANTA PILOTO
# =============================================================================

PILOT_OPERATION = {
    # Condiciones de operación típicas
    'flow_rate': 0.45,          # L/s (promedio del rango)
    'flow_rate_m3h': 1.62,      # m³/h (conversión)
    'total_volume': 0.0375,     # m³ (suma de las 3 cajas)
    'total_retention': 83.3,    # s (tiempo total de retención)
    
    # Distribución de caudales
    'rapid_mix_flow': 0.45,     # L/s
    'floc_flow': 0.45,          # L/s  
    'sed_flow': 0.65,           # L/min (0.0108 L/s)
    
    # Tiempos de retención reales
    'rapid_mix_time': 34.2,     # s (15.4L / 0.45L/s)
    'floc_time': 34.2,          # s (15.4L / 0.45L/s)
    'sed_time': 618,            # s (6.7L / 0.0108L/s) = 10.3 min
    
    # Gradientes hidráulicos calculados
    'rapid_mix_G': 825,         # s⁻¹ (promedio del rango)
    'floc_G': 40,               # s⁻¹ (promedio del rango)
    
    # Velocidades características
    'inlet_velocity': 1.15,     # m/s (en orificio 21 mm, Q=0.45 L/s)
    'upflow_velocity': 0.00025, # m/s (en sedimentador)
    'hole_velocity': 0.065      # m/s (en orificios piso falso)
}

# =============================================================================
# CONFIGURACIÓN PARA SIMULACIÓN
# =============================================================================

PILOT_SIMULATION_CONFIG = {
    # Propiedades del agua (típicas de laboratorio)
    'temperature': 20.0,        # °C (ambiente laboratorio)
    'pH': 7.2,                  # típico agua de red
    'alkalinity': 100.0,        # mg/L CaCO3
    'turbidity': 50.0,          # NTU (agua sintética)
    'initial_solids': 50.0,     # mg/L
    
    # Parámetros del sistema (escalados a dimensiones reales)
    'flow_rate': PILOT_OPERATION['flow_rate_m3h'],  # m³/h
    
    # Mezcla rápida
    'rapid_mix_volume': PILOT_PLANT_SPECS['rapid_mix']['volume'],
    'rapid_mix_G': PILOT_OPERATION['rapid_mix_G'],
    'rapid_mix_time': PILOT_OPERATION['rapid_mix_time'],
    
    # Floculación
    'floc_chambers': 1,  # Una sola cámara con bafles internos
    'floc_volume': PILOT_PLANT_SPECS['flocculation']['volume'],
    'floc_G': PILOT_OPERATION['floc_G'],
    'floc_time': PILOT_OPERATION['floc_time'],
    
    # Sedimentación
    'sed_area': PILOT_PLANT_SPECS['sedimentation']['area'],
    'sed_height': PILOT_PLANT_SPECS['sedimentation']['water_height'],
    'overflow_rate': PILOT_OPERATION['flow_rate_m3h'] / PILOT_PLANT_SPECS['sedimentation']['area'],
    
    # Coagulante (dosis típica para agua sintética)
    'coagulant_dose': 0.025     # g/L Al2(SO4)3
}

# =============================================================================
# FUNCIONES DE CÁLCULO HIDRÁULICO
# =============================================================================

def calculate_hydraulic_parameters():
    """Calcular parámetros hidráulicos del sistema piloto"""
    
    # Mezcla rápida - Pérdida de carga en deflector
    Q = PILOT_OPERATION['flow_rate'] / 1000  # m³/s
    A_orifice = np.pi * (0.021/2)**2         # m² (orificio 21 mm)
    v_jet = Q / A_orifice                    # m/s
    
    # Gradiente en mezcla rápida (correlación empírica)
    mu = 1e-3  # Pa·s (viscosidad agua 20°C)
    rho = 1000 # kg/m³
    P_dissipated = 0.5 * rho * v_jet**2 * Q  # W (potencia disipada)
    V_mix = PILOT_PLANT_SPECS['rapid_mix']['volume']
    G_rapid = np.sqrt(P_dissipated / (mu * V_mix))
    
    # Floculación - Pérdida de carga en bafles
    n_turns = PILOT_PLANT_SPECS['flocculation']['n_baffles'] - 1
    v_baffle = Q / (PILOT_PLANT_SPECS['flocculation']['opening_free'] * 
                   PILOT_PLANT_SPECS['flocculation']['water_height'])
    
    # Pérdida de carga por vuelta (correlación para bafles)
    K_loss = 2.5  # coeficiente de pérdida
    h_loss_total = n_turns * K_loss * v_baffle**2 / (2 * 9.81)
    
    # Gradiente en floculación
    P_floc = rho * 9.81 * Q * h_loss_total  # W
    V_floc = PILOT_PLANT_SPECS['flocculation']['volume']
    G_floc = np.sqrt(P_floc / (mu * V_floc))
    
    # Sedimentación - Velocidades
    A_sed = PILOT_PLANT_SPECS['sedimentation']['area']
    v_upflow = Q / A_sed  # m/s
    
    # Velocidad en orificios del piso falso
    A_holes = (PILOT_PLANT_SPECS['sedimentation']['false_floor']['total_holes'] * 
               np.pi * (PILOT_PLANT_SPECS['sedimentation']['false_floor']['hole_diameter']/2)**2)
    v_holes = Q / A_holes
    
    return {
        'rapid_mix': {
            'jet_velocity': v_jet,
            'G_calculated': G_rapid,
            'power_dissipated': P_dissipated
        },
        'flocculation': {
            'baffle_velocity': v_baffle,
            'head_loss': h_loss_total,
            'G_calculated': G_floc,
            'power_dissipated': P_floc
        },
        'sedimentation': {
            'upflow_velocity': v_upflow,
            'hole_velocity': v_holes,
            'surface_loading': Q * 3600 / A_sed  # m/h
        }
    }

def validate_pilot_design():
    """Validar el diseño hidráulico de la planta piloto"""
    
    params = calculate_hydraulic_parameters()
    
    print("VALIDACIÓN DEL DISEÑO HIDRÁULICO")
    print("=" * 50)
    
    # Mezcla rápida
    print(f"\n🔷 MEZCLA RÁPIDA:")
    print(f"Velocidad del chorro: {params['rapid_mix']['jet_velocity']:.2f} m/s")
    print(f"Gradiente G calculado: {params['rapid_mix']['G_calculated']:.0f} s⁻¹")
    print(f"Rango objetivo: {PILOT_PLANT_SPECS['rapid_mix']['G_range']} s⁻¹")
    
    G_ok = (PILOT_PLANT_SPECS['rapid_mix']['G_range'][0] <= 
            params['rapid_mix']['G_calculated'] <= 
            PILOT_PLANT_SPECS['rapid_mix']['G_range'][1])
    print(f"Estado: {'✓ CORRECTO' if G_ok else '✗ FUERA DE RANGO'}")
    
    # Floculación
    print(f"\n🔷 FLOCULACIÓN:")
    print(f"Velocidad en bafles: {params['flocculation']['baffle_velocity']:.3f} m/s")
    print(f"Gradiente G calculado: {params['flocculation']['G_calculated']:.0f} s⁻¹")
    print(f"Rango objetivo: {PILOT_PLANT_SPECS['flocculation']['G_range']} s⁻¹")
    
    G_floc_ok = (PILOT_PLANT_SPECS['flocculation']['G_range'][0] <= 
                 params['flocculation']['G_calculated'] <= 
                 PILOT_PLANT_SPECS['flocculation']['G_range'][1])
    print(f"Estado: {'✓ CORRECTO' if G_floc_ok else '✗ FUERA DE RANGO'}")
    
    # Sedimentación
    print(f"\n🔷 SEDIMENTACIÓN:")
    print(f"Velocidad ascensional: {params['sedimentation']['upflow_velocity']*1000:.2f} mm/s")
    print(f"Velocidad en orificios: {params['sedimentation']['hole_velocity']:.3f} m/s")
    print(f"Tasa de carga superficial: {params['sedimentation']['surface_loading']:.1f} m/h")
    print(f"Rango objetivo SOR: {PILOT_PLANT_SPECS['sedimentation']['SOR_range']} m/h")
    
    SOR_ok = (PILOT_PLANT_SPECS['sedimentation']['SOR_range'][0] <= 
              params['sedimentation']['surface_loading'] <= 
              PILOT_PLANT_SPECS['sedimentation']['SOR_range'][1])
    print(f"Estado: {'✓ CORRECTO' if SOR_ok else '✗ FUERA DE RANGO'}")
    
    # Velocidad en orificios (debe ser baja para no romper flóculos)
    v_hole_ok = params['sedimentation']['hole_velocity'] <= 0.10
    print(f"Velocidad orificios: {'✓ ADECUADA' if v_hole_ok else '✗ MUY ALTA'}")
    
    return params

# =============================================================================
# CONFIGURACIÓN DE ESCALAMIENTO
# =============================================================================

SCALING_FACTORS = {
    # Factores de escala típicos para plantas piloto
    'geometric_scale': 1/50,     # Escala geométrica aproximada
    'time_scale': 1/7,           # Escala temporal (Froude)
    'velocity_scale': 1/7,       # Escala de velocidades
    'flow_scale': 1/17500,       # Escala de caudales (L³)
    
    # Parámetros que se mantienen constantes
    'G_scale': 1.0,              # Gradientes se mantienen
    'concentration_scale': 1.0,   # Concentraciones se mantienen
    'temperature_scale': 1.0      # Temperatura se mantiene
}

def scale_to_full_plant(pilot_results):
    """Escalar resultados de planta piloto a planta real"""
    
    scale = SCALING_FACTORS
    
    scaled_results = {
        'flow_rate_full': pilot_results.get('flow_rate', 1.62) / scale['flow_scale'],  # m³/h
        'volume_full': PILOT_OPERATION['total_volume'] / scale['geometric_scale']**3,   # m³
        'area_full': PILOT_PLANT_SPECS['sedimentation']['area'] / scale['geometric_scale']**2,  # m²
        'time_full': PILOT_OPERATION['total_retention'] / scale['time_scale'],          # s
        
        # Los siguientes parámetros se mantienen iguales
        'efficiency': pilot_results.get('final_efficiency', 95),  # %
        'coagulant_dose': PILOT_SIMULATION_CONFIG['coagulant_dose'],  # g/L
        'G_rapid': PILOT_OPERATION['rapid_mix_G'],  # s⁻¹
        'G_floc': PILOT_OPERATION['floc_G']         # s⁻¹
    }
    
    return scaled_results

if __name__ == "__main__":
    # Validar diseño
    hydraulic_params = validate_pilot_design()
    
    # Mostrar configuración para simulación
    print(f"\n🔧 CONFIGURACIÓN PARA SIMULACIÓN:")
    print(f"Volumen mezcla rápida: {PILOT_SIMULATION_CONFIG['rapid_mix_volume']*1000:.1f} L")
    print(f"Volumen floculación: {PILOT_SIMULATION_CONFIG['floc_volume']*1000:.1f} L")
    print(f"Volumen sedimentación: {PILOT_PLANT_SPECS['sedimentation']['volume']*1000:.1f} L")
    print(f"Caudal operativo: {PILOT_SIMULATION_CONFIG['flow_rate']:.2f} m³/h")
    print(f"Tiempo total retención: {PILOT_OPERATION['total_retention']:.1f} s")