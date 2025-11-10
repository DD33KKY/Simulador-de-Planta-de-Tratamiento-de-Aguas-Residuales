"""
Script de demostración de todas las visualizaciones disponibles
Menú interactivo para elegir el tipo de visualización
"""

import os
import sys
import subprocess

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    required = ['pygame', 'matplotlib', 'numpy', 'scipy', 'pandas']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies():
    """Instalar dependencias faltantes"""
    print("🔧 Instalando dependencias...")
    try:
        subprocess.run([sys.executable, "install_game_requirements.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando dependencias")
        return False

def run_pygame_simulation():
    """Ejecutar simulación tipo juego con Pygame"""
    print("\n🎮 INICIANDO SIMULADOR TIPO JUEGO")
    print("=" * 40)
    print("Características:")
    print("• Visualización interactiva en tiempo real")
    print("• Partículas animadas moviéndose por la planta")
    print("• Controles deslizantes para ajustar parámetros")
    print("• Botones de inicio/pausa/reset")
    print("• Esquema detallado de la planta piloto")
    print("• Resultados científicos en tiempo real")
    
    input("\nPresiona Enter para continuar...")
    
    try:
        from game_visualization import WaterTreatmentGame
        game = WaterTreatmentGame()
        game.run()
    except ImportError as e:
        print(f"❌ Error importando pygame: {e}")
        print("Ejecuta 'python install_game_requirements.py' primero")
    except Exception as e:
        print(f"❌ Error ejecutando simulación: {e}")

def run_matplotlib_animation():
    """Ejecutar animación científica con Matplotlib"""
    print("\n📊 INICIANDO ANIMACIÓN CIENTÍFICA")
    print("=" * 40)
    print("Características:")
    print("• 4 gráficas simultáneas en tiempo real")
    print("• Esquema técnico de la planta piloto")
    print("• Distribución de tamaño de partículas animada")
    print("• Eficiencia de remoción en tiempo real")
    print("• Parámetros de calidad (pH, turbidez)")
    print("• Controles de teclado para ajustar parámetros")
    
    print("\nControles:")
    print("• 'q' = Salir")
    print("• 'p' = Pausar/Reanudar")
    print("• '+' = Aumentar dosis coagulante")
    print("• '-' = Disminuir dosis coagulante")
    
    input("\nPresiona Enter para continuar...")
    
    try:
        from animated_simulation import AnimatedWaterTreatment
        sim = AnimatedWaterTreatment()
        anim = sim.start_simulation()
    except ImportError as e:
        print(f"❌ Error importando matplotlib: {e}")
        print("Ejecuta 'python install_game_requirements.py' primero")
    except Exception as e:
        print(f"❌ Error ejecutando animación: {e}")

def run_basic_simulation():
    """Ejecutar simulación básica sin visualización avanzada"""
    print("\n🔬 INICIANDO SIMULACIÓN BÁSICA")
    print("=" * 40)
    print("Características:")
    print("• Simulación científica completa")
    print("• Gráficas estáticas detalladas")
    print("• Análisis de resultados")
    print("• No requiere pygame")
    
    input("\nPresiona Enter para continuar...")
    
    try:
        from pilot_plant_simulation import run_pilot_plant_analysis
        pilot_sim, results, optimization = run_pilot_plant_analysis()
        
        print("\n✅ Simulación completada exitosamente")
        print(f"Eficiencia obtenida: {results['final_efficiency']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error ejecutando simulación: {e}")

def run_test_simulation():
    """Ejecutar pruebas rápidas del sistema"""
    print("\n🧪 INICIANDO PRUEBAS DEL SISTEMA")
    print("=" * 40)
    
    try:
        from test_pilot_plant import main as test_main
        success = test_main()
        
        if success:
            print("\n✅ Todas las pruebas pasaron correctamente")
        else:
            print("\n❌ Algunas pruebas fallaron")
            
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")

def show_system_info():
    """Mostrar información del sistema"""
    print("\n📋 INFORMACIÓN DEL SISTEMA")
    print("=" * 40)
    
    # Información de Python
    print(f"🐍 Python: {sys.version}")
    
    # Verificar dependencias
    print("\n📦 DEPENDENCIAS:")
    packages = ['numpy', 'scipy', 'pandas', 'matplotlib', 'pygame']
    
    for package in packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'Desconocida')
            print(f"   ✅ {package}: {version}")
        except ImportError:
            print(f"   ❌ {package}: No instalado")
    
    # Información de archivos
    print(f"\n📁 ARCHIVOS DEL PROYECTO:")
    files = [
        'pilot_plant_config.py',
        'pilot_plant_simulation.py', 
        'game_visualization.py',
        'animated_simulation.py',
        'test_pilot_plant.py'
    ]
    
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024
            print(f"   ✅ {file}: {size:.1f} KB")
        else:
            print(f"   ❌ {file}: No encontrado")

def main_menu():
    """Menú principal de demostración"""
    
    while True:
        print("\n" + "="*60)
        print("🏭 PLANTA PILOTO DE TRATAMIENTO DE AGUA")
        print("   DEMOSTRACIÓN DE VISUALIZACIONES")
        print("="*60)
        
        print("\n🎯 OPCIONES DISPONIBLES:")
        print("1. 🎮 Simulador Interactivo (Pygame) - ¡RECOMENDADO!")
        print("2. 📊 Animación Científica (Matplotlib)")
        print("3. 🔬 Simulación Básica (Solo gráficas)")
        print("4. 🧪 Pruebas del Sistema")
        print("5. 🔧 Instalar/Verificar Dependencias")
        print("6. 📋 Información del Sistema")
        print("0. 🚪 Salir")
        
        print("\n" + "-"*60)
        
        # Verificar dependencias
        missing = check_dependencies()
        if missing:
            print(f"⚠️ Dependencias faltantes: {', '.join(missing)}")
            print("   Ejecuta la opción 5 para instalarlas")
        else:
            print("✅ Todas las dependencias están instaladas")
        
        print("-"*60)
        
        try:
            choice = input("\n🎯 Selecciona una opción (0-6): ").strip()
            
            if choice == '0':
                print("\n👋 ¡Hasta luego!")
                break
                
            elif choice == '1':
                if 'pygame' in missing:
                    print("❌ Pygame no está instalado. Ejecuta la opción 5 primero.")
                else:
                    run_pygame_simulation()
                    
            elif choice == '2':
                if 'matplotlib' in missing:
                    print("❌ Matplotlib no está instalado. Ejecuta la opción 5 primero.")
                else:
                    run_matplotlib_animation()
                    
            elif choice == '3':
                run_basic_simulation()
                
            elif choice == '4':
                run_test_simulation()
                
            elif choice == '5':
                install_dependencies()
                
            elif choice == '6':
                show_system_info()
                
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Interrumpido por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            
        input("\nPresiona Enter para volver al menú...")

def main():
    """Función principal"""
    
    print("🚀 Iniciando demostración de visualizaciones...")
    
    # Verificar que estamos en el directorio correcto
    required_files = ['pilot_plant_config.py', 'pilot_plant_simulation.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        print("Asegúrate de estar en el directorio correcto del proyecto")
        return
    
    try:
        main_menu()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()