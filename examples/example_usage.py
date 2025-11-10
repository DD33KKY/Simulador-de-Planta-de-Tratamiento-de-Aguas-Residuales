"""
Ejemplo de uso de la simulación de tratamiento de agua
Casos de estudio con diferentes condiciones
"""

import numpy as np
import matplotlib.pyplot as plt
from water_treatment_simulation import WaterTreatmentSimulation
from advanced_simulation import AdvancedWaterTreatment
from config import *

def ejemplo_basico():
    """Ejemplo básico de simulación"""
    print("="*50)
    print("EJEMPLO BÁSICO - AGUA CON TURBIDEZ MODERADA")
    print("="*50)
    
    # Crear simulación
    sim = WaterTreatmentSimulation()
    
    # Parámetros del sistema
    params = {
        'temperature': 20,      # °C
        'pH': 7.5,             # unidades pH
        'alkalinity': 120,      # mg/L CaCO3
        'turbidity': 50,        # NTU
        'initial_solids': 50,   # mg/L
        'flow_rate': 100,       # m³/h
        'rapid_mix_volume': 10, # m³
        'rapid_mix_G': 1000,    # s⁻¹
        'rapid_mix_time': 30,   # s
        'floc_chambers': 3,
        'floc_volume': 200,     # m³
        'floc_G': 50,          # s⁻¹
        'floc_time': 1800,     # s (30 min)
        'sed_area': 100,       # m²
        'sed_height': 3,       # m
        'overflow_rate': 10    # m³/m²/h
    }
    
    sim.setup_system(**params)
    
    # Ejecutar con diferentes dosis de coagulante
    dosis = [0.01, 0.02, 0.03, 0.04, 0.05]  # g/L
    eficiencias = []
    
    for dosis_coag in dosis:
        results = sim.run_simulation(coagulant_dose=dosis_coag)
        eficiencias.append(results['final_efficiency'])
        print(f"Dosis: {dosis_coag:.3f} g/L -> Eficiencia: {results['final_efficiency']:.1f}%")
    
    # Graficar curva de dosis
    plt.figure(figsize=(10, 6))
    plt.plot(dosis, eficiencias, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Dosis de Al2(SO4)3 (g/L)')
    plt.ylabel('Eficiencia de remoción (%)')
    plt.title('Curva de dosis de coagulante')
    plt.grid(True, alpha=0.3)
    plt.show()
    
    return sim, dosis, eficiencias

def ejemplo_agua_dura():
    """Ejemplo con agua de alta alcalinidad"""
    print("\n" + "="*50)
    print("EJEMPLO - AGUA DURA (ALTA ALCALINIDAD)")
    print("="*50)
    
    sim = WaterTreatmentSimulation()
    
    # Agua con alta alcalinidad
    params = {
        'temperature': 25,      # °C (agua más caliente)
        'pH': 8.2,             # pH alto
        'alkalinity': 250,      # mg/L CaCO3 (alta alcalinidad)
        'turbidity': 80,        # NTU (alta turbidez)
        'initial_solids': 80,   # mg/L
        'flow_rate': 150,       # m³/h (mayor caudal)
        'rapid_mix_volume': 15,
        'rapid_mix_G': 1200,    # Mayor intensidad de mezcla
        'rapid_mix_time': 45,
        'floc_chambers': 4,     # Más cámaras
        'floc_volume': 300,
        'floc_G': 40,          # Menor G para flóculos más grandes
        'floc_time': 2400,     # Más tiempo (40 min)
        'sed_area': 150,
        'sed_height': 4,       # Mayor altura
        'overflow_rate': 8     # Menor tasa de desborde
    }
    
    sim.setup_system(**params)
    
    # Probar dosis más alta debido a la alcalinidad
    results = sim.run_simulation(coagulant_dose=0.06)  # g/L
    
    print(f"Condiciones iniciales:")
    print(f"  pH: {results['initial']['pH']:.2f}")
    print(f"  Alcalinidad: {results['initial']['alkalinity']:.1f} mg/L CaCO3")
    print(f"  Turbidez: {results['initial']['turbidity']:.1f} NTU")
    
    print(f"\nResultados finales:")
    print(f"  pH final: {results['after_coagulation']['pH']:.2f}")
    print(f"  Alcalinidad final: {results['after_coagulation']['alkalinity']:.1f} mg/L CaCO3")
    print(f"  Eficiencia: {results['final_efficiency']:.1f}%")
    
    sim.plot_results()
    return sim

def ejemplo_agua_fria():
    """Ejemplo con agua fría (mayor viscosidad)"""
    print("\n" + "="*50)
    print("EJEMPLO - AGUA FRÍA (INVIERNO)")
    print("="*50)
    
    sim = WaterTreatmentSimulation()
    
    # Agua fría de invierno
    params = {
        'temperature': 5,       # °C (agua fría)
        'pH': 7.0,
        'alkalinity': 80,       # mg/L CaCO3
        'turbidity': 60,        # NTU
        'initial_solids': 60,   # mg/L
        'flow_rate': 80,        # m³/h (menor caudal)
        'rapid_mix_volume': 12,
        'rapid_mix_G': 1500,    # Mayor G debido a mayor viscosidad
        'rapid_mix_time': 60,   # Más tiempo
        'floc_chambers': 3,
        'floc_volume': 250,
        'floc_G': 60,          # Mayor G para compensar viscosidad
        'floc_time': 2700,     # Más tiempo (45 min)
        'sed_area': 120,
        'sed_height': 3.5,
        'overflow_rate': 6     # Menor tasa debido a menor velocidad de sedimentación
    }
    
    sim.setup_system(**params)
    
    results = sim.run_simulation(coagulant_dose=0.025)  # g/L
    
    print(f"Temperatura: {sim.water_props.temperature}°C")
    print(f"Viscosidad: {sim.water_props.viscosity*1000:.3f} mPa·s")
    print(f"Densidad: {sim.water_props.density:.1f} kg/m³")
    print(f"Eficiencia: {results['final_efficiency']:.1f}%")
    
    sim.plot_results()
    return sim

def comparacion_estacional():
    """Comparar rendimiento en diferentes estaciones"""
    print("\n" + "="*50)
    print("COMPARACIÓN ESTACIONAL")
    print("="*50)
    
    estaciones = {
        'Verano': {'temp': 25, 'pH': 7.8, 'alk': 150, 'turb': 40},
        'Otoño': {'temp': 15, 'pH': 7.2, 'alk': 120, 'turb': 70},
        'Invierno': {'temp': 5, 'pH': 7.0, 'alk': 100, 'turb': 80},
        'Primavera': {'temp': 18, 'pH': 7.4, 'alk': 130, 'turb': 60}
    }
    
    resultados_estacionales = {}
    
    for estacion, condiciones in estaciones.items():
        print(f"\nSimulando condiciones de {estacion}...")
        
        sim = WaterTreatmentSimulation()
        
        params = {
            'temperature': condiciones['temp'],
            'pH': condiciones['pH'],
            'alkalinity': condiciones['alk'],
            'turbidity': condiciones['turb'],
            'initial_solids': condiciones['turb'],
            'flow_rate': 100,
            'rapid_mix_volume': 10,
            'rapid_mix_G': 1000,
            'rapid_mix_time': 30,
            'floc_chambers': 3,
            'floc_volume': 200,
            'floc_G': 50,
            'floc_time': 1800,
            'sed_area': 100,
            'sed_height': 3,
            'overflow_rate': 10
        }
        
        sim.setup_system(**params)
        results = sim.run_simulation(coagulant_dose=0.02)
        
        resultados_estacionales[estacion] = {
            'eficiencia': results['final_efficiency'],
            'pH_final': results['after_coagulation']['pH'],
            'concentracion_final': results['sedimentation']['effluent_concentration']
        }
    
    # Graficar comparación
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    estaciones_list = list(resultados_estacionales.keys())
    eficiencias = [resultados_estacionales[est]['eficiencia'] for est in estaciones_list]
    conc_finales = [resultados_estacionales[est]['concentracion_final'] for est in estaciones_list]
    
    # Eficiencias por estación
    ax1.bar(estaciones_list, eficiencias, color=['red', 'orange', 'blue', 'green'], alpha=0.7)
    ax1.set_ylabel('Eficiencia de remoción (%)')
    ax1.set_title('Eficiencia por estación')
    ax1.set_ylim(0, 100)
    
    # Concentración final por estación
    ax2.bar(estaciones_list, conc_finales, color=['red', 'orange', 'blue', 'green'], alpha=0.7)
    ax2.set_ylabel('Concentración final (mg/L)')
    ax2.set_title('Concentración en efluente por estación')
    
    plt.tight_layout()
    plt.show()
    
    # Imprimir resumen
    print("\nRESUMEN COMPARATIVO:")
    print("-" * 40)
    for estacion, datos in resultados_estacionales.items():
        print(f"{estacion:10s}: {datos['eficiencia']:5.1f}% - {datos['concentracion_final']:5.1f} mg/L")
    
    return resultados_estacionales

def ejemplo_optimizacion():
    """Ejemplo de optimización automática"""
    print("\n" + "="*50)
    print("EJEMPLO - OPTIMIZACIÓN AUTOMÁTICA")
    print("="*50)
    
    # Usar simulación avanzada
    sim = AdvancedWaterTreatment()
    sim.setup_from_config()
    
    # Ejecutar optimización
    print("Ejecutando optimización de parámetros...")
    opt_results = sim.optimize_parameters(objective='removal_efficiency')
    
    if opt_results['success']:
        print("\nComparando con parámetros base...")
        
        # Simulación con parámetros base
        sim_base = AdvancedWaterTreatment()
        sim_base.setup_from_config()
        results_base = sim_base.run_simulation(coagulant_dose=COAGULANT['dose'])
        
        print(f"\nParámetros base:")
        print(f"  Dosis coagulante: {COAGULANT['dose']:.4f} g/L")
        print(f"  G mezcla rápida: {RAPID_MIXING['G']:.0f} s⁻¹")
        print(f"  G floculación: {FLOCCULATION['G_average']:.0f} s⁻¹")
        print(f"  Eficiencia: {results_base['final_efficiency']:.1f}%")
        
        print(f"\nParámetros optimizados:")
        opt_params = opt_results['optimal_parameters']
        print(f"  Dosis coagulante: {opt_params['coagulant_dose']:.4f} g/L")
        print(f"  G mezcla rápida: {opt_params['rapid_mix_G']:.0f} s⁻¹")
        print(f"  G floculación: {opt_params['flocculation_G']:.0f} s⁻¹")
        print(f"  Eficiencia: {opt_results['optimal_efficiency']:.1f}%")
        
        mejora = opt_results['optimal_efficiency'] - results_base['final_efficiency']
        print(f"\nMejora en eficiencia: {mejora:.1f} puntos porcentuales")
    
    return sim

def menu_ejemplos():
    """Menú interactivo para ejecutar ejemplos"""
    while True:
        print("\n" + "="*60)
        print("SIMULACIÓN DE TRATAMIENTO DE AGUA - EJEMPLOS")
        print("="*60)
        print("1. Ejemplo básico - Curva de dosis")
        print("2. Agua dura (alta alcalinidad)")
        print("3. Agua fría (invierno)")
        print("4. Comparación estacional")
        print("5. Optimización automática")
        print("6. Análisis completo avanzado")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción (0-6): ")
        
        try:
            if opcion == '1':
                ejemplo_basico()
            elif opcion == '2':
                ejemplo_agua_dura()
            elif opcion == '3':
                ejemplo_agua_fria()
            elif opcion == '4':
                comparacion_estacional()
            elif opcion == '5':
                ejemplo_optimizacion()
            elif opcion == '6':
                from advanced_simulation import run_complete_analysis
                run_complete_analysis()
            elif opcion == '0':
                print("¡Hasta luego!")
                break
            else:
                print("Opción no válida. Intente de nuevo.")
                
        except Exception as e:
            print(f"Error ejecutando ejemplo: {e}")
            print("Verifique que todas las librerías estén instaladas.")

if __name__ == "__main__":
    menu_ejemplos()