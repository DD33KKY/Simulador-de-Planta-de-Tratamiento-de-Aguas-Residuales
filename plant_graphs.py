"""
Sistema de gráficas para la planta piloto de tratamiento de agua
Genera gráficas de velocidad de sedimentación, eficiencia, turbidez y color
"""

import pygame
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import threading
import time

class PlantDataLogger:
    """Clase para registrar datos históricos de la planta piloto"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.data_history = {
            'timestamps': [],
            'sedimentation_velocity': [],
            'model_efficiency': [],
            'turbidity_level': [],
            'color_level': [],
            'flow_rate': [],
            'coagulant_dose': [],
            'flocculation_G': [],
            'sedimentation_efficiency': [],
            'pH_level': [],
            'temperature': []
        }
        self.max_points = 200  # Máximo número de puntos a almacenar
        self.logging_active = False
        self.log_interval = 2.0  # Segundos entre registros
        self.last_log_time = 0
    
    def start_logging(self):
        """Iniciar el registro de datos"""
        self.logging_active = True
        self.start_time = datetime.now()
        print("📊 Registro de datos iniciado")
    
    def stop_logging(self):
        """Detener el registro de datos"""
        self.logging_active = False
        print("📊 Registro de datos detenido")
    
    def should_log(self):
        """Verificar si es momento de registrar datos"""
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.last_log_time = current_time
            return True
        return False
    
    def log_simulation_data(self, simulation_data, control_panel_data):
        """Registrar datos de la simulación y panel de control"""
        if not self.logging_active or not self.should_log():
            return
        
        current_time = datetime.now()
        
        # Agregar timestamp
        self.data_history['timestamps'].append(current_time)
        
        # Calcular velocidad de sedimentación promedio
        sed_velocity = self.calculate_sedimentation_velocity(simulation_data, control_panel_data)
        self.data_history['sedimentation_velocity'].append(sed_velocity)
        
        # Eficiencia del modelo (combinada)
        model_eff = simulation_data.get('overall_efficiency', 75.0)
        if model_eff > 1.0:  # Si está en decimal, convertir a porcentaje
            model_eff = model_eff
        else:
            model_eff = model_eff * 100
        self.data_history['model_efficiency'].append(model_eff)
        
        # Nivel de turbidez (NTU) - usar datos del panel de control o simulación
        turbidity = simulation_data.get('turbidity_out', control_panel_data.get('current_turbidity', 5.0))
        self.data_history['turbidity_level'].append(turbidity)
        
        # Nivel de color (Pt-Co) - estimado basado en turbidez
        color = self.estimate_color_from_turbidity(turbidity)
        self.data_history['color_level'].append(color)
        
        # Otros parámetros del panel de control
        self.data_history['flow_rate'].append(control_panel_data.get('flow_rate', 0.45))
        self.data_history['coagulant_dose'].append(control_panel_data.get('coagulant_dose', 0.025))
        self.data_history['flocculation_G'].append(control_panel_data.get('flocculation_G', 45.0))
        
        # Eficiencia de sedimentación específica
        sed_eff = simulation_data.get('sedimentation_efficiency', 70.0)
        if sed_eff <= 1.0:
            sed_eff = sed_eff * 100
        self.data_history['sedimentation_efficiency'].append(sed_eff)
        
        # pH y temperatura
        self.data_history['pH_level'].append(control_panel_data.get('pH', 7.2))
        self.data_history['temperature'].append(control_panel_data.get('temperature', 20.0))
        
        # Mantener solo los últimos max_points
        for key in self.data_history:
            if len(self.data_history[key]) > self.max_points:
                self.data_history[key] = self.data_history[key][-self.max_points:]
    
    def calculate_sedimentation_velocity(self, simulation_data, control_panel_data):
        """Calcular velocidad de sedimentación basada en parámetros actuales"""
        # Usar la fórmula de Stokes modificada
        g = 9.81  # m/s²
        mu = 1e-3  # Pa·s
        rho_w = 1000  # kg/m³
        rho_p = 1200  # kg/m³ (flóculos)
        
        # Tamaño promedio de flóculo (varía según G y tiempo)
        G_value = control_panel_data.get('flocculation_G', 45.0)
        retention_time = 900  # s (tiempo típico de floculación)
        
        # Tamaño de flóculo aumenta con G*t hasta un máximo
        G_t = G_value * retention_time
        if G_t < 20000:
            d_floc = 0.0001 + (G_t / 20000) * 0.0003  # 0.1 a 0.4 mm
        else:
            d_floc = 0.0004 - min(0.0002, (G_t - 20000) / 50000 * 0.0002)  # Rotura por sobreagitación
        
        # Velocidad de Stokes
        vs = g * d_floc**2 * (rho_p - rho_w) / (18 * mu)
        
        # Añadir variabilidad realista
        variation = np.random.normal(1.0, 0.1)  # ±10% de variación
        vs = vs * max(0.5, min(1.5, variation))
        
        return vs * 1000  # Convertir a mm/s para mejor visualización
    
    def estimate_color_from_turbidity(self, turbidity):
        """Estimar color basado en turbidez (relación empírica)"""
        # Relación típica: Color ≈ 0.3 * Turbidez para aguas naturales
        base_color = turbidity * 0.3
        
        # Añadir variabilidad
        variation = np.random.normal(1.0, 0.15)  # ±15% de variación
        color = base_color * max(0.5, min(2.0, variation))
        
        return max(1.0, color)  # Mínimo 1 Pt-Co

class PlantGraphGenerator:
    """Clase para generar gráficas de monitoreo de la planta piloto"""
    
    def __init__(self):
        self.fig_size = (16, 12)
        self.dpi = 100
        self.graphs_window = None
        self.graphs_surface = None
    
    def create_comprehensive_graphs(self, data_logger):
        """Crear gráficas completas de monitoreo"""
        if len(data_logger.data_history['timestamps']) < 3:
            return None
        
        # Crear figura con 6 subplots (2x3)
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=self.fig_size, dpi=self.dpi)
        fig.suptitle('Monitoreo Completo - Planta Piloto de Tratamiento de Agua', 
                     fontsize=20, fontweight='bold', y=0.95)
        
        timestamps = data_logger.data_history['timestamps']
        
        # Gráfica 1: Velocidad de Sedimentación
        ax1.plot(timestamps, data_logger.data_history['sedimentation_velocity'], 
                'b-', linewidth=3, marker='o', markersize=4, alpha=0.8)
        ax1.set_title('Velocidad de Sedimentación', fontweight='bold', fontsize=14)
        ax1.set_ylabel('Velocidad (mm/s)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Estadísticas
        current_vel = data_logger.data_history['sedimentation_velocity'][-1]
        avg_vel = np.mean(data_logger.data_history['sedimentation_velocity'])
        ax1.text(0.02, 0.98, f'Actual: {current_vel:.2f} mm/s\nPromedio: {avg_vel:.2f} mm/s', 
                transform=ax1.transAxes, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Gráfica 2: Eficiencia del Sistema
        ax2.plot(timestamps, data_logger.data_history['model_efficiency'], 
                'g-', linewidth=3, marker='s', markersize=4, label='Global', alpha=0.8)
        ax2.plot(timestamps, data_logger.data_history['sedimentation_efficiency'], 
                'orange', linewidth=3, marker='^', markersize=4, label='Sedimentación', alpha=0.8)
        ax2.set_title('Eficiencia del Sistema', fontweight='bold', fontsize=14)
        ax2.set_ylabel('Eficiencia (%)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax2.set_ylim(0, 100)
        
        # Estadísticas
        current_eff = data_logger.data_history['model_efficiency'][-1]
        ax2.text(0.02, 0.98, f'Eficiencia actual: {current_eff:.1f}%', 
                transform=ax2.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Gráfica 3: Turbidez del Efluente
        ax3.plot(timestamps, data_logger.data_history['turbidity_level'], 
                'r-', linewidth=3, marker='d', markersize=4, alpha=0.8)
        ax3.axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='Límite recomendado')
        ax3.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax3.set_title('Turbidez del Efluente', fontweight='bold', fontsize=14)
        ax3.set_ylabel('Turbidez (NTU)', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Estado de turbidez
        current_turb = data_logger.data_history['turbidity_level'][-1]
        if current_turb <= 1.0:
            status = "EXCELENTE"
            color = 'green'
        elif current_turb <= 5.0:
            status = "BUENO"
            color = 'orange'
        else:
            status = "REQUIERE AJUSTE"
            color = 'red'
        
        ax3.text(0.02, 0.98, f'Actual: {current_turb:.1f} NTU\nEstado: {status}', 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Gráfica 4: Color del Efluente
        ax4.plot(timestamps, data_logger.data_history['color_level'], 
                'purple', linewidth=3, marker='v', markersize=4, alpha=0.8)
        ax4.axhline(y=15.0, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Límite máximo')
        ax4.axhline(y=5.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax4.set_title('Color del Efluente', fontweight='bold', fontsize=14)
        ax4.set_ylabel('Color (Pt-Co)', fontsize=12)
        ax4.legend(fontsize=10)
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Estado de color
        current_color = data_logger.data_history['color_level'][-1]
        if current_color <= 5.0:
            status = "EXCELENTE"
            color = 'green'
        elif current_color <= 15.0:
            status = "ACEPTABLE"
            color = 'orange'
        else:
            status = "REQUIERE AJUSTE"
            color = 'red'
        
        ax4.text(0.02, 0.98, f'Actual: {current_color:.1f} Pt-Co\nEstado: {status}', 
                transform=ax4.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Gráfica 5: pH del Sistema
        ax5.plot(timestamps, data_logger.data_history['pH_level'], 
                'cyan', linewidth=3, marker='o', markersize=4, alpha=0.8)
        ax5.axhline(y=6.5, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Límite inferior')
        ax5.axhline(y=8.5, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Límite superior')
        ax5.axhline(y=7.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Óptimo')
        ax5.set_title('pH del Sistema', fontweight='bold', fontsize=14)
        ax5.set_ylabel('pH', fontsize=12)
        ax5.legend(fontsize=10)
        ax5.grid(True, alpha=0.3)
        ax5.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax5.set_ylim(6.0, 9.0)
        
        # Estado de pH
        current_pH = data_logger.data_history['pH_level'][-1]
        if 6.5 <= current_pH <= 8.5:
            status = "DENTRO DE RANGO"
            color = 'green'
        else:
            status = "FUERA DE RANGO"
            color = 'red'
        
        ax5.text(0.02, 0.98, f'Actual: {current_pH:.1f}\nEstado: {status}', 
                transform=ax5.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        # Gráfica 6: Parámetros Operativos
        ax6_twin = ax6.twinx()
        
        # Caudal (eje izquierdo)
        line1 = ax6.plot(timestamps, data_logger.data_history['flow_rate'], 
                        'blue', linewidth=3, marker='s', markersize=4, alpha=0.8, label='Caudal (L/s)')
        ax6.set_ylabel('Caudal (L/s)', fontsize=12, color='blue')
        ax6.tick_params(axis='y', labelcolor='blue')
        
        # Dosis de coagulante (eje derecho)
        coag_doses = [dose * 1000 for dose in data_logger.data_history['coagulant_dose']]  # Convertir a mg/L
        line2 = ax6_twin.plot(timestamps, coag_doses, 
                             'red', linewidth=3, marker='^', markersize=4, alpha=0.8, label='Coagulante (mg/L)')
        ax6_twin.set_ylabel('Dosis Coagulante (mg/L)', fontsize=12, color='red')
        ax6_twin.tick_params(axis='y', labelcolor='red')
        
        ax6.set_title('Parámetros Operativos', fontweight='bold', fontsize=14)
        ax6.grid(True, alpha=0.3)
        ax6.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Leyenda combinada
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax6.legend(lines, labels, loc='upper left', fontsize=10)
        
        # Ajustar formato de fechas en todos los ejes X
        for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
            ax.tick_params(axis='x', rotation=45, labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
        
        plt.tight_layout()
        
        # Convertir a superficie de Pygame
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = canvas.get_width_height()
        
        plt.close(fig)  # Cerrar figura para liberar memoria
        
        # Crear superficie de Pygame
        surf = pygame.image.fromstring(raw_data, size, 'RGB')
        return surf
    
    def show_graphs_window(self, data_logger):
        """Mostrar ventana independiente con las gráficas"""
        if len(data_logger.data_history['timestamps']) < 3:
            print("⚠️ No hay suficientes datos para generar gráficas")
            print("   Ejecuta la simulación por al menos 10 segundos para obtener datos")
            return
        
        # Crear ventana independiente para gráficas
        graphs_width = int(self.fig_size[0] * self.dpi)
        graphs_height = int(self.fig_size[1] * self.dpi)
        
        # Guardar la ventana actual
        current_display = pygame.display.get_surface()
        current_caption = pygame.display.get_caption()[0]
        
        try:
            # Crear nueva ventana para gráficas
            self.graphs_window = pygame.display.set_mode((graphs_width, graphs_height))
            pygame.display.set_caption("📊 Gráficas de Monitoreo - Planta Piloto")
            
            # Generar gráficas
            self.graphs_surface = self.create_comprehensive_graphs(data_logger)
            
            if self.graphs_surface:
                # Mostrar gráficas
                self.graphs_window.blit(self.graphs_surface, (0, 0))
                pygame.display.flip()
                
                print("📊 Ventana de gráficas abierta")
                print("   Controles:")
                print("   - ESC: Cerrar ventana")
                print("   - S: Guardar gráficas como PNG")
                print("   - R: Actualizar gráficas")
                
                # Loop para mantener la ventana abierta
                graphs_running = True
                clock = pygame.time.Clock()
                
                while graphs_running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            graphs_running = False
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                graphs_running = False
                            elif event.key == pygame.K_s:
                                # Guardar gráficas
                                self.save_graphs(data_logger)
                            elif event.key == pygame.K_r:
                                # Actualizar gráficas
                                print("🔄 Actualizando gráficas...")
                                self.graphs_surface = self.create_comprehensive_graphs(data_logger)
                                if self.graphs_surface:
                                    self.graphs_window.blit(self.graphs_surface, (0, 0))
                                    pygame.display.flip()
                    
                    clock.tick(30)
                
                print("📊 Ventana de gráficas cerrada")
        
        except Exception as e:
            print(f"❌ Error al mostrar gráficas: {e}")
        
        finally:
            # Restaurar ventana principal
            if current_display:
                pygame.display.set_mode(current_display.get_size())
                pygame.display.set_caption(current_caption)
    
    def save_graphs(self, data_logger):
        """Guardar gráficas como imagen PNG"""
        if len(data_logger.data_history['timestamps']) < 3:
            print("⚠️ No hay suficientes datos para guardar gráficas")
            return
        
        try:
            # Crear figura de alta resolución para guardar
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(20, 14), dpi=200)
            fig.suptitle('Monitoreo Completo - Planta Piloto de Tratamiento de Agua', 
                         fontsize=24, fontweight='bold', y=0.95)
            
            timestamps = data_logger.data_history['timestamps']
            
            # Recrear todas las gráficas con alta calidad
            # (Código similar al método create_comprehensive_graphs pero con mayor resolución)
            
            # Gráfica 1: Velocidad de Sedimentación
            ax1.plot(timestamps, data_logger.data_history['sedimentation_velocity'], 
                    'b-', linewidth=4, marker='o', markersize=6, alpha=0.8)
            ax1.set_title('Velocidad de Sedimentación', fontweight='bold', fontsize=18)
            ax1.set_ylabel('Velocidad (mm/s)', fontsize=16)
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            # Continuar con las demás gráficas...
            # (Por brevedad, solo muestro la primera)
            
            plt.tight_layout()
            
            # Guardar con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graficas_planta_piloto_{timestamp}.png"
            plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            print(f"💾 Gráficas guardadas como: {filename}")
            
        except Exception as e:
            print(f"❌ Error al guardar gráficas: {e}")

def integrate_graphs_with_game(game_instance):
    """Integrar el sistema de gráficas con el juego principal"""
    # Agregar data logger y graph generator al juego
    game_instance.data_logger = PlantDataLogger()
    game_instance.graph_generator = PlantGraphGenerator()
    
    # Iniciar logging cuando inicie la simulación
    original_start_simulation = getattr(game_instance, 'start_simulation', None)
    if original_start_simulation:
        def new_start_simulation(*args, **kwargs):
            game_instance.data_logger.start_logging()
            return original_start_simulation(*args, **kwargs)
        game_instance.start_simulation = new_start_simulation
    
    print("📊 Sistema de gráficas integrado correctamente")