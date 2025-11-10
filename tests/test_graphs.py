"""
Script de prueba para el sistema de gráficas de la planta piloto
"""

import pygame
import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_visualization import WaterTreatmentGame

def main():
    """Función principal para probar las gráficas"""
    print("🧪 Iniciando prueba del sistema de gráficas...")
    print("=" * 50)
    
    try:
        # Inicializar el juego
        game = WaterTreatmentGame()
        
        print("✅ Juego inicializado correctamente")
        print("📊 Sistema de gráficas disponible")
        print()
        print("INSTRUCCIONES:")
        print("1. Presiona 'INICIAR' para comenzar la simulación")
        print("2. Espera al menos 10-15 segundos para generar datos")
        print("3. Presiona 'GENERAR GRAFICAS' para ver las gráficas")
        print("4. En la ventana de gráficas:")
        print("   - ESC: Cerrar ventana de gráficas")
        print("   - S: Guardar gráficas como PNG")
        print("   - R: Actualizar gráficas con nuevos datos")
        print()
        print("🚀 Iniciando simulador...")
        
        # Ejecutar el juego
        game.run()
        
    except Exception as e:
        print(f"❌ Error al ejecutar la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()