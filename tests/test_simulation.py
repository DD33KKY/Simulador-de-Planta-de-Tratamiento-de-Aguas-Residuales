"""
Script de prueba simple para verificar que la simulación funciona
"""

from water_treatment_simulation import WaterTreatmentSimulation

def test_basic_simulation():
    """Prueba básica de la simulación"""
    print("Iniciando prueba de simulación básica...")
    
    # Crear simulación
    sim = WaterTreatmentSimulation()
    
    # Parámetros simples
    params = {
        'temperature': 20,
        'pH': 7.5,
        'alkalinity': 120,
        'turbidity': 50,
        'initial_solids': 50,
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
    
    # Configurar sistema
    sim.setup_system(**params)
    
    # Ejecutar simulación
    results = sim.run_simulation(coagulant_dose=0.02)
    
    # Mostrar resultados básicos
    print("\nResultados de la simulación:")
    print(f"pH inicial: {results['initial']['pH']:.2f}")
    print(f"pH final: {results['after_coagulation']['pH']:.2f}")
    print(f"Alcalinidad inicial: {results['initial']['alkalinity']:.1f} mg/L CaCO3")
    print(f"Alcalinidad final: {results['after_coagulation']['alkalinity']:.1f} mg/L CaCO3")
    print(f"Turbidez inicial: {results['initial']['turbidity']:.1f} NTU")
    print(f"Concentración final: {results['sedimentation']['effluent_concentration']:.1f} mg/L")
    print(f"Eficiencia de remoción: {results['final_efficiency']:.1f}%")
    
    # Generar gráficas
    print("\nGenerando gráficas...")
    sim.plot_results()
    
    print("\nPrueba completada exitosamente!")
    return True

if __name__ == "__main__":
    try:
        test_basic_simulation()
    except Exception as e:
        print(f"Error en la simulación: {e}")
        import traceback
        traceback.print_exc()