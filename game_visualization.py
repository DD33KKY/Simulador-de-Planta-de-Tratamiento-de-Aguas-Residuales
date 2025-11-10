"""
Visualización interactiva tipo juego de la planta piloto de tratamiento de agua
Muestra el flujo de agua y partículas en tiempo real
"""

import pygame
import numpy as np
import math
import random
from pilot_plant_simulation import PilotPlantSimulation
from pilot_plant_config import PILOT_PLANT_SPECS, PILOT_OPERATION, calculate_hydraulic_parameters
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from plant_graphs import PlantDataLogger, PlantGraphGenerator

# Inicializar Pygame
pygame.init()

# Obtener información de la pantalla del usuario
display_info = pygame.display.Info()
screen_width_available = display_info.current_w
screen_height_available = display_info.current_h

# Calcular tamaño óptimo de ventana (80% del tamaño de pantalla, con límites)
SCREEN_WIDTH = min(1400, int(screen_width_available * 0.8))
SCREEN_HEIGHT = min(850, int(screen_height_available * 0.85))

# Asegurar tamaños mínimos
SCREEN_WIDTH = max(1000, SCREEN_WIDTH)
SCREEN_HEIGHT = max(650, SCREEN_HEIGHT)

print(f"Resolucion detectada: {screen_width_available}x{screen_height_available}")
print(f"Ventana ajustada: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Planta Piloto de Tratamiento de Agua - Simulador Interactivo")

# Layout adaptativo basado en el tamaño de la ventana
HEADER_HEIGHT = int(SCREEN_HEIGHT * 0.06)  # 6% de la altura
HEADER_AREA = pygame.Rect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT)

# Distribución de áreas (proporcional al tamaño de pantalla)
margin = int(SCREEN_WIDTH * 0.015)  # 1.5% de margen
control_panel_width = int(SCREEN_WIDTH * 0.30)  # 30% para panel de control
main_area_width = SCREEN_WIDTH - control_panel_width - 3 * margin

# Altura de áreas
results_panel_height = int(SCREEN_HEIGHT * 0.27)  # 27% para resultados
main_area_height = SCREEN_HEIGHT - HEADER_HEIGHT - results_panel_height - 3 * margin

MAIN_AREA = pygame.Rect(margin, HEADER_HEIGHT + margin, main_area_width, main_area_height)
CONTROL_PANEL = pygame.Rect(main_area_width + 2 * margin, HEADER_HEIGHT + margin, 
                            control_panel_width, SCREEN_HEIGHT - HEADER_HEIGHT - 2 * margin)
RESULTS_PANEL = pygame.Rect(margin, SCREEN_HEIGHT - results_panel_height - margin, 
                            main_area_width, results_panel_height)

# Colores
COLORS = {
    'background': (20, 30, 50),
    'water_clean': (100, 150, 255),
    'water_dirty': (139, 115, 85),
    'water_medium': (120, 140, 180),
    'particle_small': (255, 255, 0),
    'particle_medium': (255, 165, 0),
    'particle_large': (255, 69, 0),
    'floc': (160, 82, 45),
    'tank_border': (200, 200, 200),
    'pipe': (100, 100, 100),
    'baffle': (150, 150, 150),
    'text': (255, 255, 255),
    'button': (70, 130, 180),
    'button_hover': (100, 149, 237),
    'success': (0, 255, 0),
    'warning': (255, 255, 0),
    'error': (255, 0, 0)
}

# Fuentes adaptativas (escalan según el tamaño de pantalla)
font_scale = min(SCREEN_WIDTH / 1200, SCREEN_HEIGHT / 750)  # Factor de escala
font_large = pygame.font.Font(None, int(36 * font_scale))
font_medium = pygame.font.Font(None, int(24 * font_scale))
font_small = pygame.font.Font(None, int(18 * font_scale))

class Particle:
    """Clase para representar partículas en el agua"""
    
    def __init__(self, x, y, size=1.0, particle_type='clay'):
        self.x = x
        self.y = y
        self.size = size  # μm
        self.particle_type = particle_type
        self.velocity_x = 0
        self.velocity_y = 0
        self.age = 0
        self.coagulated = False
        self.flocculated = False
        
    def get_color(self):
        """Obtener color según tamaño y tipo"""
        if self.flocculated:
            return COLORS['floc']
        elif self.size < 1:
            return COLORS['particle_small']
        elif self.size < 10:
            return COLORS['particle_medium']
        else:
            return COLORS['particle_large']
    
    def get_radius(self):
        """Obtener radio visual (escalado)"""
        return max(1, min(8, int(math.log10(self.size + 1) * 3)))
    
    def update(self, dt, flow_field=None):
        """Actualizar posición de la partícula"""
        if flow_field:
            self.velocity_x = flow_field.get('vx', 0)
            self.velocity_y = flow_field.get('vy', 0)
        
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.age += dt
    
    def draw(self, surface):
        """Dibujar partícula"""
        color = self.get_color()
        radius = self.get_radius()
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), radius)

class DataLogger:
    """Clase para registrar datos históricos de la planta"""
    
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
            'sedimentation_efficiency': []
        }
        self.max_points = 100  # Máximo número de puntos a almacenar
    
    def log_data(self, simulation_data):
        """Registrar datos de la simulación"""
        current_time = datetime.now()
        
        # Agregar timestamp
        self.data_history['timestamps'].append(current_time)
        
        # Calcular velocidad de sedimentación promedio
        sed_velocity = self.calculate_sedimentation_velocity(simulation_data)
        self.data_history['sedimentation_velocity'].append(sed_velocity)
        
        # Eficiencia del modelo (combinada)
        model_eff = simulation_data.get('overall_efficiency', 0.75) * 100
        self.data_history['model_efficiency'].append(model_eff)
        
        # Nivel de turbidez (NTU)
        turbidity = simulation_data.get('turbidity_out', 5.0)
        self.data_history['turbidity_level'].append(turbidity)
        
        # Nivel de color (Pt-Co)
        color = simulation_data.get('color_out', 15.0)
        self.data_history['color_level'].append(color)
        
        # Otros parámetros
        self.data_history['flow_rate'].append(simulation_data.get('flow_rate', 0.45))
        self.data_history['coagulant_dose'].append(simulation_data.get('coagulant_dose', 0.025))
        self.data_history['flocculation_G'].append(simulation_data.get('flocculation_G', 45.0))
        self.data_history['sedimentation_efficiency'].append(simulation_data.get('sedimentation_efficiency', 0.70) * 100)
        
        # Mantener solo los últimos max_points
        for key in self.data_history:
            if len(self.data_history[key]) > self.max_points:
                self.data_history[key] = self.data_history[key][-self.max_points:]
    
    def calculate_sedimentation_velocity(self, simulation_data):
        """Calcular velocidad de sedimentación basada en parámetros actuales"""
        # Usar la fórmula de Stokes modificada
        g = 9.81  # m/s²
        mu = 1e-3  # Pa·s
        rho_w = 1000  # kg/m³
        rho_p = 1200  # kg/m³ (flóculos)
        
        # Tamaño promedio de flóculo (varía según G y tiempo)
        G_value = simulation_data.get('flocculation_G', 45.0)
        retention_time = simulation_data.get('flocculation_time', 900)  # s
        
        # Tamaño de flóculo aumenta con G*t hasta un máximo
        G_t = G_value * retention_time
        if G_t < 20000:
            d_floc = 0.0001 + (G_t / 20000) * 0.0003  # 0.1 a 0.4 mm
        else:
            d_floc = 0.0004 - min(0.0002, (G_t - 20000) / 50000 * 0.0002)  # Rotura por sobreagitación
        
        # Velocidad de Stokes
        vs = g * d_floc**2 * (rho_p - rho_w) / (18 * mu)
        
        return vs * 1000  # Convertir a mm/s para mejor visualización

class GraphGenerator:
    """Clase para generar gráficas de los datos de la planta"""
    
    def __init__(self):
        self.fig_size = (14, 10)
        self.dpi = 100
        self.graphs_window = None
        self.graphs_surface = None
    
    def create_graphs_window(self, data_logger):
        """Crear ventana con las 4 gráficas principales"""
        if len(data_logger.data_history['timestamps']) < 2:
            return None
        
        # Crear figura con subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.fig_size, dpi=self.dpi)
        fig.suptitle('Monitoreo de Planta Piloto de Tratamiento de Agua', fontsize=18, fontweight='bold')
        
        timestamps = data_logger.data_history['timestamps']
        
        # Gráfica 1: Velocidad de Sedimentación
        ax1.plot(timestamps, data_logger.data_history['sedimentation_velocity'], 
                'b-', linewidth=3, marker='o', markersize=5)
        ax1.set_title('Velocidad de Sedimentación', fontweight='bold', fontsize=14)
        ax1.set_ylabel('Velocidad (mm/s)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Añadir estadísticas
        current_vel = data_logger.data_history['sedimentation_velocity'][-1]
        avg_vel = np.mean(data_logger.data_history['sedimentation_velocity'])
        ax1.text(0.02, 0.98, f'Actual: {current_vel:.2f} mm/s\nPromedio: {avg_vel:.2f} mm/s', 
                transform=ax1.transAxes, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Gráfica 2: Eficiencia del Modelo
        ax2.plot(timestamps, data_logger.data_history['model_efficiency'], 
                'g-', linewidth=3, marker='s', markersize=5, label='Global')
        ax2.plot(timestamps, data_logger.data_history['sedimentation_efficiency'], 
                'orange', linewidth=3, marker='^', markersize=5, label='Sedimentación')
        ax2.set_title('Eficiencia del Sistema', fontweight='bold', fontsize=14)
        ax2.set_ylabel('Eficiencia (%)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Añadir estadísticas
        current_eff = data_logger.data_history['model_efficiency'][-1]
        ax2.text(0.02, 0.98, f'Eficiencia actual: {current_eff:.1f}%', 
                transform=ax2.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Gráfica 3: Nivel de Turbidez
        ax3.plot(timestamps, data_logger.data_history['turbidity_level'], 
                'r-', linewidth=3, marker='d', markersize=5)
        ax3.axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='Límite recomendado')
        ax3.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax3.set_title('Turbidez del Efluente', fontweight='bold', fontsize=14)
        ax3.set_ylabel('Turbidez (NTU)', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Añadir estadísticas y estado
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
        
        # Gráfica 4: Color
        ax4.plot(timestamps, data_logger.data_history['color_level'], 
                'purple', linewidth=3, marker='v', markersize=5)
        ax4.axhline(y=15.0, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Límite máximo')
        ax4.axhline(y=5.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax4.set_title('Color del Efluente', fontweight='bold', fontsize=14)
        ax4.set_ylabel('Color (Pt-Co)', fontsize=12)
        ax4.legend(fontsize=10)
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Añadir estadísticas y estado
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
        
        # Ajustar formato de fechas en eje X
        for ax in [ax1, ax2, ax3, ax4]:
            ax.tick_params(axis='x', rotation=45, labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        
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
        if len(data_logger.data_history['timestamps']) < 2:
            print("⚠️ No hay suficientes datos para generar gráficas")
            return
        
        # Crear ventana independiente para gráficas
        graphs_width = int(self.fig_size[0] * self.dpi)
        graphs_height = int(self.fig_size[1] * self.dpi)
        
        self.graphs_window = pygame.display.set_mode((graphs_width, graphs_height))
        pygame.display.set_caption("Gráficas de Monitoreo - Planta Piloto")
        
        # Generar gráficas
        self.graphs_surface = self.create_graphs_window(data_logger)
        
        if self.graphs_surface:
            # Mostrar gráficas
            self.graphs_window.blit(self.graphs_surface, (0, 0))
            pygame.display.flip()
            
            print("📊 Ventana de gráficas abierta - Presiona ESC para cerrar")
            
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
                
                clock.tick(30)
            
            # Cerrar ventana de gráficas
            pygame.display.quit()
            pygame.display.init()
            
            # Restaurar ventana principal
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Planta Piloto de Tratamiento de Agua - Simulador Interactivo")
            
            print("📊 Ventana de gráficas cerrada")
    
    def save_graphs(self, data_logger):
        """Guardar gráficas como imagen PNG"""
        if len(data_logger.data_history['timestamps']) < 2:
            return
        
        # Crear figura para guardar
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), dpi=150)
        fig.suptitle('Monitoreo de Planta Piloto de Tratamiento de Agua', fontsize=20, fontweight='bold')
        
        timestamps = data_logger.data_history['timestamps']
        
        # Gráfica 1: Velocidad de Sedimentación
        ax1.plot(timestamps, data_logger.data_history['sedimentation_velocity'], 
                'b-', linewidth=3, marker='o', markersize=6)
        ax1.set_title('Velocidad de Sedimentación', fontweight='bold', fontsize=16)
        ax1.set_ylabel('Velocidad (mm/s)', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Gráfica 2: Eficiencia del Modelo
        ax2.plot(timestamps, data_logger.data_history['model_efficiency'], 
                'g-', linewidth=3, marker='s', markersize=6, label='Global')
        ax2.plot(timestamps, data_logger.data_history['sedimentation_efficiency'], 
                'orange', linewidth=3, marker='^', markersize=6, label='Sedimentación')
        ax2.set_title('Eficiencia del Sistema', fontweight='bold', fontsize=16)
        ax2.set_ylabel('Eficiencia (%)', fontsize=14)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Gráfica 3: Nivel de Turbidez
        ax3.plot(timestamps, data_logger.data_history['turbidity_level'], 
                'r-', linewidth=3, marker='d', markersize=6)
        ax3.axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='Límite recomendado')
        ax3.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax3.set_title('Turbidez del Efluente', fontweight='bold', fontsize=16)
        ax3.set_ylabel('Turbidez (NTU)', fontsize=14)
        ax3.legend(fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Gráfica 4: Color
        ax4.plot(timestamps, data_logger.data_history['color_level'], 
                'purple', linewidth=3, marker='v', markersize=6)
        ax4.axhline(y=15.0, color='red', linestyle='--', alpha=0.7, linewidth=2, label='Límite máximo')
        ax4.axhline(y=5.0, color='green', linestyle='--', alpha=0.7, linewidth=2, label='Excelente')
        ax4.set_title('Color del Efluente', fontweight='bold', fontsize=16)
        ax4.set_ylabel('Color (Pt-Co)', fontsize=14)
        ax4.legend(fontsize=12)
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Ajustar formato
        for ax in [ax1, ax2, ax3, ax4]:
            ax.tick_params(axis='x', rotation=45, labelsize=12)
            ax.tick_params(axis='y', labelsize=12)
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        
        plt.tight_layout()
        
        # Guardar con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"graficas_planta_piloto_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"💾 Gráficas guardadas como: {filename}")

class WaterFlow:
    """Clase para manejar el flujo de agua"""
    
    def __init__(self):
        self.flow_rate = 0.45  # L/s
        self.particles = []
        self.flow_vectors = {}
        
    def add_particle(self, x, y, size=None):
        """Añadir nueva partícula"""
        if size is None:
            size = np.random.lognormal(0, 1)  # Distribución log-normal
        particle = Particle(x, y, size)
        self.particles.append(particle)
    
    def update_flow_field(self, tank_type, tank_bounds):
        """Actualizar campo de flujo según el tipo de tanque"""
        x1, y1, x2, y2 = tank_bounds
        
        if tank_type == 'rapid_mix':
            # Flujo turbulento con recirculación
            center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
            self.flow_vectors = {
                'vx': 50 * math.cos(time.time() * 5),
                'vy': 30 * math.sin(time.time() * 3),
                'turbulence': True
            }
        
        elif tank_type == 'flocculation':
            # Flujo laminar con bafles
            self.flow_vectors = {
                'vx': 20,
                'vy': 10 * math.sin(time.time() * 2),
                'turbulence': False
            }
        
        elif tank_type == 'sedimentation':
            # Flujo ascendente lento
            self.flow_vectors = {
                'vx': 5,
                'vy': -15,  # Ascendente
                'turbulence': False
            }
    
    def coagulate_particles(self, coagulant_dose):
        """Simular coagulación de partículas"""
        for particle in self.particles:
            if not particle.coagulated and random.random() < coagulant_dose * 10:
                particle.coagulated = True
                particle.size *= 1.2  # Ligero crecimiento
    
    def flocculate_particles(self, G_value):
        """Simular floculación"""
        # Buscar partículas cercanas para agregar
        for i, p1 in enumerate(self.particles):
            if p1.coagulated and not p1.flocculated:
                for j, p2 in enumerate(self.particles[i+1:], i+1):
                    if p2.coagulated and not p2.flocculated:
                        distance = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
                        if distance < 20 and random.random() < G_value / 1000:
                            # Formar flóculo
                            p1.flocculated = True
                            p1.size = math.sqrt(p1.size**2 + p2.size**2)
                            self.particles.remove(p2)
                            break
    
    def settle_particles(self):
        """Simular sedimentación"""
        for particle in self.particles:
            if particle.flocculated:
                # Velocidad de sedimentación proporcional al tamaño
                settling_velocity = particle.size * 0.1
                particle.velocity_y += settling_velocity

def calculate_flocculation_efficiency(G_value, retention_time, n_baffles, coagulant_dose=0.025):
    """
    Calcular eficiencia de floculación basándose en parámetros hidráulicos
    
    Ecuación basada en:
    - G value (gradiente de velocidad): controla la frecuencia de colisiones
    - Tiempo de retención: tiempo disponible para formación de flóculos
    - Número de bafles: afecta la mezcla y formación de flóculos
    - Dosis de coagulante: afecta la eficiencia de coagulación
    
    Referencia: Camp & Stein (1943), Smoluchowski (1917)
    """
    # Rango óptimo de G para floculación: 20-75 s⁻¹
    # Rango óptimo de G*t (criterio de Camp): 10,000 - 100,000
    
    G_t = G_value * retention_time  # Criterio de Camp
    
    # Eficiencia base basada en G*t
    if G_t < 5000:
        base_efficiency = 0.15  # G*t muy bajo, floculación pobre
    elif G_t < 20000:
        base_efficiency = 0.25 + (G_t - 5000) / 15000 * 0.15  # 0.25 a 0.40
    elif G_t < 50000:
        base_efficiency = 0.40 + (G_t - 20000) / 30000 * 0.20  # 0.40 a 0.60 (óptimo)
    elif G_t < 100000:
        base_efficiency = 0.60 - (G_t - 50000) / 50000 * 0.15  # 0.60 a 0.45 (sobreagitación)
    else:
        base_efficiency = 0.30  # G*t muy alto, rotura de flóculos
    
    # Factor de corrección por número de bafles (más bafles = mejor mezcla)
    baffle_factor = 1.0 + (n_baffles - 1) * 0.05  # Hasta 1.30 para 7 bafles
    
    # Factor de corrección por dosis de coagulante
    # Dosis óptima típica: 0.02-0.05 g/L
    if coagulant_dose < 0.01:
        coag_factor = 0.7  # Dosis muy baja
    elif coagulant_dose < 0.05:
        coag_factor = 0.8 + (coagulant_dose - 0.01) / 0.04 * 0.2  # 0.8 a 1.0
    else:
        coag_factor = 1.0 - min(0.2, (coagulant_dose - 0.05) / 0.05 * 0.2)  # Sobredosis reduce eficiencia
    
    # Eficiencia final
    efficiency = base_efficiency * baffle_factor * coag_factor
    
    # Limitar entre 0.20 y 0.50 (rango realista para floculación)
    efficiency = max(0.20, min(0.50, efficiency))
    
    return efficiency


def calculate_sedimentation_efficiency(surface_loading_rate, retention_time, height, 
                                       initial_turbidity=50.0, floc_density=1200):
    """
    Calcular eficiencia de sedimentación basándose en parámetros físicos
    
    Ecuación basada en:
    - Surface Overflow Rate (SOR): velocidad ascensional del agua
    - Tiempo de retención: tiempo disponible para sedimentación
    - Altura del tanque: distancia de sedimentación
    - Turbidez inicial: afecta la sedimentación obstaculizada
    
    Referencia: Hazen (1904), Camp (1946), teoría de sedimentación discreta
    """
    # Velocidad de sedimentación típica para flóculos (Stokes modificado)
    # Asumir tamaño promedio de flóculo: 0.1-1.0 mm después de floculación
    g = 9.81  # m/s²
    mu = 1e-3  # Pa·s (viscosidad agua 20°C)
    rho_w = 1000  # kg/m³
    rho_p = floc_density  # kg/m³ (densidad de flóculos)
    
    # Tamaño promedio de flóculo (asumir distribución log-normal)
    # Después de floculación, flóculos típicamente 0.2-0.5 mm
    d_floc = 0.0003  # m (0.3 mm - tamaño promedio de flóculo)
    
    # Velocidad de sedimentación (Stokes modificado)
    # Re < 0.1: usar Stokes puro
    vs_stokes = g * d_floc**2 * (rho_p - rho_w) / (18 * mu)
    
    # Verificar Re
    Re = rho_w * vs_stokes * d_floc / mu
    if Re > 0.1:
        # Corrección para Re > 0.1 (Schiller-Naumann)
        Cd = 24/Re + 3/np.sqrt(Re) + 0.34
        vs = np.sqrt(4 * g * d_floc * (rho_p - rho_w) / (3 * Cd * rho_w))
    else:
        vs = vs_stokes
    
    # Aplicar sedimentación obstaculizada (Richardson-Zaki)
    # Concentración aproximada de sólidos (asumir turbidez ≈ TSS en mg/L)
    concentration = initial_turbidity  # mg/L (aproximado)
    phi = concentration / 1000000  # Fracción volumétrica (muy pequeña para agua)
    n = 4.65  # Exponente de Richardson-Zaki
    vs_hindered = vs * (1 - phi)**n
    
    # Eficiencia basada en relación entre velocidad de sedimentación y velocidad ascensional
    # Si vs > v_upflow, las partículas sedimentan
    v_upflow = surface_loading_rate / 3600  # m/s (convertir de m/h a m/s)
    
    # Eficiencia de remoción: relación entre velocidad de sedimentación y altura del tanque
    # removal = min(1.0, vs_hindered * retention_time / height)
    removal_ratio = min(1.0, vs_hindered * retention_time / height)
    
    # Factor de corrección por SOR (Surface Overflow Rate)
    # SOR óptimo para sedimentación: 20-40 m/h
    if surface_loading_rate < 20:
        sor_factor = 0.95  # SOR muy bajo, excelente sedimentación
    elif surface_loading_rate < 40:
        sor_factor = 1.0 - (surface_loading_rate - 20) / 20 * 0.15  # 1.0 a 0.85
    elif surface_loading_rate < 60:
        sor_factor = 0.85 - (surface_loading_rate - 40) / 20 * 0.20  # 0.85 a 0.65
    else:
        sor_factor = 0.60  # SOR muy alto, sedimentación pobre
    
    # Eficiencia final
    efficiency = removal_ratio * sor_factor
    
    # Ajustar según tiempo de retención
    # Tiempo mínimo recomendado: 1-2 horas (3600-7200 s)
    if retention_time < 1800:  # < 30 min
        time_factor = 0.7
    elif retention_time < 3600:  # 30-60 min
        time_factor = 0.8 + (retention_time - 1800) / 1800 * 0.15  # 0.8 a 0.95
    else:
        time_factor = 0.95 + min(0.05, (retention_time - 3600) / 3600 * 0.05)  # 0.95 a 1.0
    
    efficiency = efficiency * time_factor
    
    # Limitar entre 0.50 y 0.85 (rango realista para sedimentación)
    efficiency = max(0.50, min(0.85, efficiency))
    
    return efficiency


class Tank:
    """Clase para representar cada tanque de la planta con dimensiones reales"""
    
    def __init__(self, x, y, real_length, real_width, real_height, tank_type, name, scale=10):
        # Dimensiones reales en metros convertidas a píxeles
        self.real_length = real_length  # m
        self.real_width = real_width    # m  
        self.real_height = real_height  # m
        self.scale = scale  # píxeles por cm
        
        # Dimensiones en píxeles (convertir m a cm y luego escalar)
        self.width = int(real_length * 100 * scale / 5)   # Largo visual (más grande)
        self.height = int(real_width * 100 * scale / 5)   # Ancho visual (profundidad)  
        self.depth = int(real_height * 100 * scale / 5)   # Altura visual
        
        self.x = x
        self.y = y
        self.tank_type = tank_type
        self.name = name
        self.water_level = self.depth * 0.94  # 15.5cm de 16.5cm total
        self.efficiency = 0
        self.particles_in = 0
        self.particles_out = 0
        
        # Parámetros hidráulicos reales (se calcularán dinámicamente)
        self.hydraulic_params = {
            'flow_rate': 0.45,  # L/s
            'velocity': 0.0,    # m/s
            'gradient_G': 0.0,  # s⁻¹
            'head_loss': 0.0,   # m
            'power_dissipated': 0.0,  # W
            'retention_time': 0.0,   # s
            'reynolds': 0.0
        }
        
        # Conexiones específicas según tu diseño
        self.inlet_pipe = None
        self.outlet_pipe = None
        self.setup_connections()
        
        # Calcular parámetros hidráulicos iniciales
        self.update_hydraulic_parameters()
        
    def update_hydraulic_parameters(self, flow_rate=None):
        """Calcular parámetros hidráulicos reales basados en las especificaciones"""
        if flow_rate is None:
            flow_rate = PILOT_OPERATION['flow_rate'] / 1000  # Convertir L/s a m³/s
        else:
            flow_rate = flow_rate / 1000  # Convertir L/s a m³/s
        
        # Propiedades del agua
        mu = 1e-3  # Pa·s (viscosidad agua 20°C)
        rho = 1000  # kg/m³
        
        if self.tank_type == 'rapid_mix':
            # Mezcla rápida - Cálculo real usando dimensiones REALES del tanque
            # Dimensiones reales: 23×23×24 cm (ancho×largo×alto)
            Q = flow_rate  # m³/s
            
            # Calcular volumen REAL del tanque (23×23×24 cm, altura útil ~23 cm)
            length_m = self.real_length  # 0.23 m
            width_m = self.real_width    # 0.23 m
            water_height_m = self.real_height * 0.96  # 0.24 * 0.96 = ~0.23 m (altura útil)
            V_mix = length_m * width_m * water_height_m  # m³ (volumen REAL)
            
            # Área del orificio de entrada (20-22 mm, usar 21 mm promedio)
            d_orifice = 0.021  # m
            A_orifice = np.pi * (d_orifice/2)**2  # m²
            v_jet = Q / A_orifice  # m/s
            
            # Potencia disipada por el chorro
            P_dissipated = 0.5 * rho * v_jet**2 * Q  # W
            
            # Gradiente G usando volumen REAL
            G_rapid = np.sqrt(P_dissipated / (mu * V_mix))  # s⁻¹
            
            # Tiempo de retención usando volumen REAL
            retention_time = V_mix / Q  # s
            
            # Número de Reynolds
            Re = rho * v_jet * d_orifice / mu
            
            self.hydraulic_params = {
                'flow_rate': Q * 1000,  # L/s
                'velocity': v_jet,      # m/s
                'gradient_G': G_rapid,  # s⁻¹
                'head_loss': 0.0,       # No hay pérdida de carga significativa en mezcla rápida
                'power_dissipated': P_dissipated,  # W
                'retention_time': retention_time,   # s
                'reynolds': Re,
                'orifice_diameter': d_orifice * 1000  # mm
            }
            
        elif self.tank_type == 'flocculation':
            # Floculación - Cálculo real usando dimensiones REALES del tanque
            # Dimensiones reales: 30×14×24 cm (ancho×largo×alto)
            specs = PILOT_PLANT_SPECS['flocculation']  # Para obtener parámetros de bafles
            Q = flow_rate  # m³/s
            
            # Calcular volumen REAL del tanque (30×14×24 cm, altura útil ~23 cm)
            length_m = self.real_length  # 0.30 m
            width_m = self.real_width    # 0.14 m
            water_height_m = self.real_height * 0.96  # 0.24 * 0.96 = ~0.23 m (altura útil)
            V_floc = length_m * width_m * water_height_m  # m³ (volumen REAL)
            
            # Velocidad en bafles (usar opening_free de specs, pero ajustar si es necesario)
            opening_free = specs['opening_free']  # m (4.4 cm)
            water_height = water_height_m  # Usar altura real calculada
            v_baffle = Q / (opening_free * water_height)  # m/s
            
            # Pérdida de carga en bafles
            n_turns = specs['n_baffles'] - 1  # 6 vueltas
            K_loss = 2.5  # coeficiente de pérdida
            h_loss_total = n_turns * K_loss * v_baffle**2 / (2 * 9.81)  # m
            
            # Potencia disipada
            P_floc = rho * 9.81 * Q * h_loss_total  # W
            
            # Gradiente G usando volumen REAL
            G_floc = np.sqrt(P_floc / (mu * V_floc))  # s⁻¹
            
            # Tiempo de retención usando volumen REAL
            retention_time = V_floc / Q  # s
            
            # Número de Reynolds
            Re = rho * v_baffle * opening_free / mu
            
            self.hydraulic_params = {
                'flow_rate': Q * 1000,  # L/s
                'velocity': v_baffle,    # m/s
                'gradient_G': G_floc,   # s⁻¹
                'head_loss': h_loss_total,  # m
                'power_dissipated': P_floc,  # W
                'retention_time': retention_time,  # s
                'reynolds': Re,
                'n_baffles': specs['n_baffles']
            }
            
        elif self.tank_type == 'sedimentation':
            # Sedimentación - Cálculo real usando dimensiones REALES del tanque
            # Dimensiones reales: 30×14×24 cm (ancho×largo×alto)
            specs = PILOT_PLANT_SPECS['sedimentation']  # Para obtener parámetros del piso falso
            Q = flow_rate  # m³/s
            
            # Calcular área REAL del tanque (30×14 cm)
            length_m = self.real_length  # 0.30 m
            width_m = self.real_width     # 0.14 m
            A_sed = length_m * width_m  # m² (área REAL)
            
            # Calcular volumen REAL del tanque (30×14×24 cm, altura útil ~23 cm)
            water_height_m = self.real_height * 0.96  # 0.24 * 0.96 = ~0.23 m (altura útil)
            V_sed = length_m * width_m * water_height_m  # m³ (volumen REAL)
            
            # Velocidad ascensional usando área REAL
            v_upflow = Q / A_sed  # m/s
            
            # Velocidad en orificios del piso falso
            n_holes = specs['false_floor']['total_holes']  # 55 orificios
            d_hole = specs['false_floor']['hole_diameter']  # 0.002 m (2 mm)
            A_holes = n_holes * np.pi * (d_hole/2)**2  # m²
            v_holes = Q / A_holes  # m/s
            
            # Tasa de carga superficial (SOR) usando área REAL
            surface_loading = Q * 3600 / A_sed  # m/h
            
            # Tiempo de retención usando volumen REAL
            retention_time = V_sed / Q  # s
            
            # Número de Reynolds
            Re = rho * v_upflow * np.sqrt(A_sed) / mu
            
            self.hydraulic_params = {
                'flow_rate': Q * 1000,  # L/s
                'velocity': v_upflow,    # m/s (velocidad ascensional)
                'gradient_G': 0.0,      # No hay gradiente en sedimentación
                'head_loss': 0.0,       # Pérdida despreciable
                'power_dissipated': 0.0,  # W
                'retention_time': retention_time,  # s
                'reynolds': Re,
                'surface_loading': surface_loading,  # m/h
                'hole_velocity': v_holes,  # m/s
                'n_holes': n_holes
            }
        
    def setup_connections(self):
        """Configurar conexiones específicas según el diseño real"""
        if self.tank_type == 'rapid_mix':
            # Entrada lateral izquierda, salida por ventana derecha
            self.inlet_pipe = {
                'x': self.x - 20,
                'y': self.y + self.depth // 2,
                'diameter': 20,  # Orificio 20-22mm
                'type': 'horizontal_jet'
            }
            self.outlet_pipe = {
                'x': self.x + self.width,
                'y': self.y + self.depth - 30,  # 12.5cm del fondo
                'width': self.width,
                'height': 30,  # 3cm de alto
                'type': 'overflow_weir'
            }
            
        elif self.tank_type == 'flocculation':
            # Entrada por ventana izquierda, salida por ventana derecha
            self.inlet_pipe = {
                'x': self.x,
                'y': self.y + self.depth - 30,
                'width': self.width,
                'height': 30,
                'type': 'overflow_weir'
            }
            self.outlet_pipe = {
                'x': self.x + self.width,
                'y': self.y + self.depth - 30,
                'width': self.width, 
                'height': 30,
                'type': 'overflow_weir'
            }
            
        elif self.tank_type == 'sedimentation':
            # Entrada por ventana izquierda, salida por tubos superiores
            self.inlet_pipe = {
                'x': self.x,
                'y': self.y + self.depth - 30,
                'width': self.width,
                'height': 30,
                'type': 'overflow_weir'
            }
            self.outlet_pipe = {
                'x': self.x + self.width // 2,
                'y': self.y + 10,  # Tubos en la parte superior
                'type': 'collection_tubes',
                'n_tubes': 3
            }
    
    def get_bounds(self):
        """Obtener límites del tanque"""
        return (self.x, self.y, self.x + self.width, self.y + self.depth)
    
    def draw(self, surface):
        """Dibujar tanque con vista isométrica realista"""
        
        # Dibujar tanque en 3D isométrico
        self.draw_isometric_tank(surface)
        
        # Agua con nivel realista
        water_color = self.get_water_color()
        self.draw_water_level(surface, water_color)
        
        # Elementos específicos del tanque
        if self.tank_type == 'rapid_mix':
            self.draw_rapid_mix_elements(surface)
        elif self.tank_type == 'flocculation':
            self.draw_flocculation_elements(surface)
        elif self.tank_type == 'sedimentation':
            self.draw_sedimentation_elements(surface)
        
        # Conexiones de tuberías
        self.draw_pipe_connections(surface)
        
        # Etiquetas con información real
        self.draw_labels(surface)
    
    def draw_isometric_tank(self, surface):
        """Dibujar tanque en vista isométrica 3D"""
        
        # Definir puntos para vista isométrica
        iso_factor = 0.5  # Factor de perspectiva isométrica
        
        # Cara frontal (rectángulo principal)
        front_rect = pygame.Rect(self.x, self.y, self.width, self.depth)
        pygame.draw.rect(surface, COLORS['tank_border'], front_rect, 3)
        
        # Cara superior (perspectiva)
        top_points = [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width + self.height * iso_factor, self.y - self.height * iso_factor),
            (self.x + self.height * iso_factor, self.y - self.height * iso_factor)
        ]
        pygame.draw.polygon(surface, COLORS['tank_border'], top_points)
        pygame.draw.polygon(surface, COLORS['tank_border'], top_points, 2)
        
        # Cara lateral derecha
        side_points = [
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.depth),
            (self.x + self.width + self.height * iso_factor, self.y + self.depth - self.height * iso_factor),
            (self.x + self.width + self.height * iso_factor, self.y - self.height * iso_factor)
        ]
        pygame.draw.polygon(surface, COLORS['tank_border'], side_points)
        pygame.draw.polygon(surface, COLORS['tank_border'], side_points, 2)
    
    def draw_water_level(self, surface, water_color):
        """Dibujar nivel de agua realista"""
        
        # Agua en cara frontal
        water_height = self.water_level
        water_y = self.y + self.depth - water_height
        
        water_rect = pygame.Rect(self.x + 3, water_y, self.width - 6, water_height - 3)
        pygame.draw.rect(surface, water_color, water_rect)
        
        # Superficie del agua (cara superior)
        iso_factor = 0.5
        water_surface_points = [
            (self.x + 3, water_y),
            (self.x + self.width - 3, water_y),
            (self.x + self.width - 3 + self.height * iso_factor, water_y - self.height * iso_factor),
            (self.x + 3 + self.height * iso_factor, water_y - self.height * iso_factor)
        ]
        
        # Color más claro para la superficie
        surface_color = tuple(min(255, c + 30) for c in water_color)
        pygame.draw.polygon(surface, surface_color, water_surface_points)
        
        # Agua en cara lateral
        side_water_points = [
            (self.x + self.width - 3, water_y),
            (self.x + self.width - 3, self.y + self.depth - 3),
            (self.x + self.width - 3 + self.height * iso_factor, self.y + self.depth - 3 - self.height * iso_factor),
            (self.x + self.width - 3 + self.height * iso_factor, water_y - self.height * iso_factor)
        ]
        
        # Color más oscuro para el lateral
        side_color = tuple(max(0, c - 20) for c in water_color)
        pygame.draw.polygon(surface, side_color, side_water_points)
    
    def draw_pipe_connections(self, surface):
        """Dibujar conexiones de tuberías reales"""
        
        if self.inlet_pipe:
            if self.inlet_pipe['type'] == 'horizontal_jet':
                # Tubería de entrada horizontal (PVC 1/2")
                pipe_rect = pygame.Rect(
                    self.inlet_pipe['x'], 
                    self.inlet_pipe['y'] - 5,
                    25, 10
                )
                pygame.draw.rect(surface, COLORS['pipe'], pipe_rect)
                
                # Orificio de entrada
                pygame.draw.circle(surface, COLORS['background'], 
                                 (self.x, self.inlet_pipe['y']), 
                                 self.inlet_pipe['diameter'] // 4)
                
            elif self.inlet_pipe['type'] == 'overflow_weir':
                # Ventana de conexión
                weir_rect = pygame.Rect(
                    self.inlet_pipe['x'] - 5,
                    self.inlet_pipe['y'],
                    10,
                    self.inlet_pipe['height']
                )
                pygame.draw.rect(surface, COLORS['water_clean'], weir_rect)
        
        if self.outlet_pipe:
            if self.outlet_pipe['type'] == 'overflow_weir':
                # Ventana de salida
                weir_rect = pygame.Rect(
                    self.outlet_pipe['x'],
                    self.outlet_pipe['y'],
                    10,
                    self.outlet_pipe['height']
                )
                pygame.draw.rect(surface, COLORS['water_clean'], weir_rect)
                
            elif self.outlet_pipe['type'] == 'collection_tubes':
                # Tubos de recolección (3 tubos PVC 1/2")
                for i in range(self.outlet_pipe['n_tubes']):
                    tube_x = self.x + 20 + i * (self.width - 40) // 2
                    tube_rect = pygame.Rect(tube_x - 3, self.outlet_pipe['y'], 6, 30)
                    pygame.draw.rect(surface, COLORS['pipe'], tube_rect)
                    
                    # Perforaciones en tubos
                    for j in range(3):
                        hole_y = self.outlet_pipe['y'] + 5 + j * 8
                        pygame.draw.circle(surface, COLORS['background'], 
                                         (tube_x, hole_y), 2)
    
    def draw_labels(self, surface):
        """Dibujar etiquetas con información real sin superposición"""
        
        # Área de texto arriba del tanque (ajustado dinámicamente)
        label_y_start = self.y - int(90 * font_scale)
        
        # Nombre del tanque (compacto)
        name_parts = self.name.split(' - ')
        name_short = name_parts[1] if len(name_parts) > 1 else self.name
        name_text = font_small.render(name_short, True, (200, 220, 255))
        name_rect = name_text.get_rect(centerx=self.x + self.width//2, y=label_y_start)
        surface.blit(name_text, name_rect)
        
        # Dimensiones reales (más compactas)
        dimensions = f"{self.real_length*100:.0f}x{self.real_width*100:.0f}x{self.real_height*100:.0f}cm"
        dim_text = font_small.render(dimensions, True, (180, 180, 180))
        dim_rect = dim_text.get_rect(centerx=self.x + self.width//2, y=label_y_start + int(18 * font_scale))
        surface.blit(dim_text, dim_rect)
        
        # Área de texto abajo del tanque (compacto)
        info_y_start = self.y + self.depth + int(8 * font_scale)
        
        # Información del proceso (compacta) - DATOS REALES + DINÁMICOS
        info_lines = []
        
        if self.tank_type == 'rapid_mix':
            info_lines = [
                f"G: {self.hydraulic_params['gradient_G']:.0f} s-1",
                f"v: {self.hydraulic_params['velocity']:.2f} m/s"
            ]
        elif self.tank_type == 'flocculation':
            info_lines = [
                f"G: {self.hydraulic_params['gradient_G']:.0f} s-1",
                f"Δh: {self.hydraulic_params['head_loss']*1000:.1f} mm"
            ]
        elif self.tank_type == 'sedimentation':
            info_lines = [
                f"SOR: {self.hydraulic_params['surface_loading']:.1f} m/h",
                f"v: {self.hydraulic_params['velocity']*1000:.2f} mm/s"
            ]
        
        # Añadir turbidez y pH si están disponibles
        if hasattr(self, 'current_turbidity'):
            info_lines.append(f"Turb: {self.current_turbidity:.0f} NTU")
        if hasattr(self, 'current_pH'):
            info_lines.append(f"pH: {self.current_pH:.1f}")
        
        # Eficiencia con color
        eff_color = COLORS['success'] if self.efficiency > 90 else COLORS['warning'] if self.efficiency > 70 else COLORS['error']
        
        for i, line in enumerate(info_lines):
            color = (150, 200, 255) if 'G:' in line or 'v:' in line or 'SOR:' in line else (180, 180, 180)
            info_surface = font_small.render(line, True, color)
            info_rect = info_surface.get_rect(centerx=self.x + self.width//2, y=info_y_start + i * int(16 * font_scale))
            surface.blit(info_surface, info_rect)
        
        # Eficiencia en la última línea
        eff_text = f"Efic: {self.efficiency:.0f}%"
        eff_surface = font_small.render(eff_text, True, eff_color)
        eff_rect = eff_surface.get_rect(centerx=self.x + self.width//2, y=info_y_start + len(info_lines) * int(16 * font_scale))
        surface.blit(eff_surface, eff_rect)
    
    def get_water_color(self):
        """Obtener color del agua según la turbidez"""
        # El color se actualiza dinámicamente desde el game
        if hasattr(self, 'current_turbidity'):
            turbidity = self.current_turbidity
            
            # Interpolar color según turbidez (0-50 NTU)
            if turbidity <= 1:
                # Agua muy limpia (azul claro)
                return (100, 150, 255)
            elif turbidity <= 5:
                # Agua limpia (azul)
                return (110, 145, 240)
            elif turbidity <= 15:
                # Agua medio limpia (azul grisáceo)
                return (120, 140, 200)
            elif turbidity <= 30:
                # Agua turbia media (gris azulado)
                return (130, 130, 160)
            else:
                # Agua turbia (marrón grisáceo)
                t_factor = min(1.0, (turbidity - 30) / 20)
                r = int(130 + (139 - 130) * t_factor)
                g = int(130 + (115 - 130) * t_factor)
                b = int(160 + (85 - 160) * t_factor)
                return (r, g, b)
        else:
            # Fallback basado en eficiencia
            if self.efficiency > 90:
                return COLORS['water_clean']
            elif self.efficiency > 50:
                return COLORS['water_medium']
            else:
                return COLORS['water_dirty']
    
    def draw_rapid_mix_elements(self, surface):
        """Dibujar elementos de mezcla rápida con dimensiones reales"""
        
        # Tabique separador (3 cm de la pared de entrada) - según especificaciones
        tabique_x = self.x + int(0.03 * 100 * self.scale / 5)  # 3 cm escalado
        pygame.draw.line(surface, COLORS['baffle'],
                        (tabique_x, self.y + 15), 
                        (tabique_x, self.y + self.depth - 15), 6)
        
        # Deflector de acrílico 8×8 cm a 2 cm del chorro (según especificaciones reales)
        # El deflector está a 2 cm del orificio de entrada (20-22 mm)
        deflector_size = int(0.08 * 100 * self.scale / 5)  # 8 cm escalado
        deflector_x = self.x + int(0.02 * 100 * self.scale / 5) + 10  # 2 cm del chorro + margen
        deflector_y = self.y + (self.depth - deflector_size) // 2
        
        # Dibujar deflector como cuadrado 8×8 cm (acrílico transparente simulado)
        deflector_rect = pygame.Rect(deflector_x, deflector_y, deflector_size, deflector_size)
        # Color turquesa/azul claro como en la imagen
        deflector_color = (64, 224, 208)  # Turquesa
        pygame.draw.rect(surface, deflector_color, deflector_rect)
        pygame.draw.rect(surface, COLORS['baffle'], deflector_rect, 2)  # Borde
        
        # Indicar que es el deflector
        deflector_label = font_small.render("8×8 cm", True, COLORS['text'])
        surface.blit(deflector_label, (deflector_x, deflector_y - 15))
        
        # Chorro de entrada animado (Ø 20-22 mm) - según especificaciones reales
        if hasattr(self, 'inlet_pipe'):
            jet_x = self.x
            jet_y = self.inlet_pipe['y']
            
            # Diámetro del orificio: 20-22 mm (usar 21 mm promedio)
            orifice_diameter_px = int(0.021 * 100 * self.scale / 5)  # Escalado
            
            # Animación del chorro turbulento
            jet_intensity = 1 + 0.3 * math.sin(time.time() * 15)
            jet_length = int(30 * jet_intensity)
            jet_width = max(2, orifice_diameter_px // 2)
            
            # Chorro principal (horizontal desde la entrada)
            pygame.draw.line(surface, COLORS['water_clean'],
                           (jet_x, jet_y), (jet_x + jet_length, jet_y), jet_width)
            
            # Mostrar orificio de entrada
            pygame.draw.circle(surface, COLORS['water_clean'], 
                             (jet_x, jet_y), orifice_diameter_px // 2, 2)
            
            # Turbulencia alrededor del deflector (mezcla rápida)
            for i in range(8):
                turb_x = deflector_x + deflector_size // 2 + random.randint(-15, 15)
                turb_y = deflector_y + deflector_size // 2 + random.randint(-15, 15)
                turb_radius = random.randint(2, 5)
                # Partículas de agua en movimiento
                alpha_color = (*COLORS['water_medium'], 150)  # Semi-transparente
                pygame.draw.circle(surface, COLORS['water_medium'], 
                                 (turb_x, turb_y), turb_radius, 1)
        
        # Ventana de salida (3 cm alto, todo el ancho, 12.5 cm del fondo)
        outlet_y = self.y + int(self.depth * 0.25)  # Proporcional
        outlet_rect = pygame.Rect(self.x + self.width - 8, outlet_y, 15, int(self.depth * 0.3))
        pygame.draw.rect(surface, COLORS['water_clean'], outlet_rect)
        
        # Indicador visual de dosificación de coagulante (sulfato de aluminio)
        # El coagulante se añade en la mezcla rápida y se distribuye con el agua
        # Relación: 10 unidades de coagulante por cada 4 litros de agua
        coagulant_indicator_x = self.x + self.width // 2
        coagulant_indicator_y = self.y + self.depth - 40
        
        # Dibujar símbolo de dosificación (gotas de coagulante cayendo)
        for i in range(3):
            drop_x = coagulant_indicator_x - 15 + i * 15
            drop_y = coagulant_indicator_y + int(5 * math.sin(time.time() * 3 + i))
            # Gotas cayendo (color amarillo/beige para el coagulante)
            pygame.draw.circle(surface, (255, 200, 100), (drop_x, drop_y), 3)
            pygame.draw.circle(surface, (255, 220, 120), (drop_x, drop_y), 2)
        
        # Etiqueta de dosificación (se calcula dinámicamente desde el game)
        # La relación es: 10 de coagulante por cada 4 litros de agua
        if hasattr(self, 'coagulant_dose_display'):
            dose_text = f"Dosis: {self.coagulant_dose_display:.1f} (10/4L)"
            dose_label = font_small.render(dose_text, True, (255, 200, 100))
            surface.blit(dose_label, (self.x + 5, self.y + self.depth + 5))
    
    def draw_flocculation_elements(self, surface):
        """Dibujar bafles de floculación con dimensiones exactas"""
        
        # 7 bafles de acrílico 3mm, separación 3.3 cm
        # Ajustar espaciado según ancho real del tanque
        n_baffles = 7
        available_width = max(80, self.width - 40)  # Dejar márgenes, mínimo 80px
        baffle_spacing = available_width // (n_baffles + 1)  # Espaciado dinámico
        baffle_thickness = 4
        
        for i in range(n_baffles):
            baffle_x = self.x + 20 + i * baffle_spacing  # Margen inicial
            
            # Alturas alternadas según especificación (ajustadas a escala)
            if i % 2 == 0:
                # Paso inferior: desde abajo
                baffle_y1 = self.y + self.depth - 5   # Holgura inferior
                baffle_y2 = self.y + self.depth // 3  # Altura del bafle
            else:
                # Paso superior: desde arriba
                baffle_y1 = self.y + 5  # Holgura superior
                baffle_y2 = self.y + 2 * self.depth // 3  # Altura del bafle
            
            # Dibujar bafle
            baffle_rect = pygame.Rect(baffle_x, baffle_y2, baffle_thickness, baffle_y1 - baffle_y2)
            pygame.draw.rect(surface, COLORS['baffle'], baffle_rect)
            
            # Abertura libre (ajustada a escala)
            opening_y = baffle_y1 if i % 2 == 0 else baffle_y2
            opening_height = self.depth // 4  # Abertura proporcional
            
            # Indicar flujo a través de la abertura
            if i < 6:  # No en el último bafle
                flow_y = opening_y + (opening_height // 2 if i % 2 == 0 else -opening_height // 2)
                
                # Flecha de flujo animada
                arrow_offset = int(time.time() * 50) % 20
                arrow_x = baffle_x + 10 + arrow_offset
                
                if self.x + 10 <= arrow_x <= self.x + self.width - 20:
                    # Dibujar flecha de flujo
                    pygame.draw.polygon(surface, COLORS['water_medium'], [
                        (arrow_x, flow_y - 3),
                        (arrow_x + 8, flow_y),
                        (arrow_x, flow_y + 3),
                        (arrow_x + 3, flow_y)
                    ])
        
        # Mostrar patrón de flujo alternado
        flow_path_color = (*COLORS['water_clean'], 100)  # Semi-transparente
        
        # Líneas de flujo serpenteante
        for i in range(6):
            start_x = self.x + 15 + i * baffle_spacing + 5
            end_x = self.x + 15 + (i + 1) * baffle_spacing - 5
            
            if i % 2 == 0:
                # Flujo por abajo
                flow_y = self.y + self.depth - 20
            else:
                # Flujo por arriba  
                flow_y = self.y + 20
            
            pygame.draw.line(surface, COLORS['water_medium'],
                           (start_x, flow_y), (end_x, flow_y), 2)
    
    def draw_sedimentation_elements(self, surface):
        """Dibujar elementos de sedimentación con especificaciones exactas"""
        
        # Piso falso: 1.0 cm sobre el fondo, acrílico 3mm
        false_floor_y = self.y + self.depth - 15  # 1 cm del fondo (escalado)
        
        # Placa del piso falso (28.8 × 14.8 cm) - ajustada al tanque
        floor_width = max(20, int(self.width * 0.9))  # 90% del ancho del tanque, mínimo 20px
        floor_height = max(10, int(self.height * 0.9))  # 90% de la profundidad del tanque
        
        floor_rect = pygame.Rect(
            self.x + (self.width - floor_width) // 2,
            false_floor_y - 5,  # 3mm espesor (escalado)
            floor_width,
            5
        )
        pygame.draw.rect(surface, COLORS['baffle'], floor_rect)
        
        # 55 orificios Ø2mm, separación 2.5cm, márgenes 1.5cm (ajustado)
        hole_spacing = max(5, floor_width // 8)  # Espaciado dinámico
        margin = max(2, floor_width // 10)       # Margen proporcional
        
        # Calcular distribución de orificios (asegurar valores positivos)
        available_width = max(10, floor_width - 2 * margin)
        available_height = max(10, floor_height - 2 * margin)
        
        holes_x = max(1, int(available_width // hole_spacing) + 1)
        holes_y = max(1, int(available_height // hole_spacing) + 1)
        
        hole_count = 0
        for i in range(holes_x):
            for j in range(holes_y):
                if hole_count >= 55:  # Máximo 55 orificios
                    break
                    
                hole_x = floor_rect.x + margin + i * hole_spacing
                hole_y = floor_rect.y + margin + j * hole_spacing
                
                # Dibujar orificio
                pygame.draw.circle(surface, COLORS['background'], 
                                 (hole_x, false_floor_y), 3)
                
                # Flujo ascendente a través del orificio (animado)
                if random.random() < 0.3:  # 30% de probabilidad por frame
                    bubble_y = hole_y - random.randint(10, 30)
                    pygame.draw.circle(surface, COLORS['water_clean'], 
                                     (hole_x, bubble_y), 1)
                
                hole_count += 1
        
        # Entrada inferior: PVC 1/2" con codo 90°
        inlet_pipe_rect = pygame.Rect(
            self.x - 15, 
            self.y + self.depth - 5,
            20, 8
        )
        pygame.draw.rect(surface, COLORS['pipe'], inlet_pipe_rect)
        
        # Codo 90° hacia el plenum
        codo_rect = pygame.Rect(
            self.x - 5,
            self.y + self.depth - 15,
            8, 15
        )
        pygame.draw.rect(surface, COLORS['pipe'], codo_rect)
        
        # Plenum (espacio bajo el piso falso)
        plenum_rect = pygame.Rect(
            self.x + 5,
            false_floor_y,
            self.width - 10,
            10
        )
        pygame.draw.rect(surface, COLORS['water_medium'], plenum_rect, 1)
        
        # 3 tubos de recolección PVC 1/2" en la parte superior
        tube_spacing = self.width // 4
        for i in range(3):
            tube_x = self.x + tube_spacing + i * tube_spacing
            
            # Tubo vertical
            tube_rect = pygame.Rect(tube_x - 4, self.y + 15, 8, 50)
            pygame.draw.rect(surface, COLORS['pipe'], tube_rect)
            
            # 8 orificios Ø3mm en los 3 cm superiores
            for j in range(6):
                hole_y = self.y + 20 + j * 6  # Distribuidos en los tubos
                pygame.draw.circle(surface, COLORS['background'], 
                                 (tube_x, hole_y), 3)
        
        # Colector superior PVC 3/4"
        collector_rect = pygame.Rect(
            self.x + 10,
            self.y + 5,
            self.width - 20,
            8
        )
        pygame.draw.rect(surface, COLORS['pipe'], collector_rect)
        
        # Tees 3/4" × 1/2" (conexiones de los tubos)
        for i in range(3):
            tube_x = self.x + tube_spacing + i * tube_spacing
            tee_rect = pygame.Rect(tube_x - 4, self.y + 5, 8, 8)
            pygame.draw.rect(surface, COLORS['pipe'], tee_rect)
        
        # Mostrar flujo ascendente con partículas sedimentando
        self.draw_sedimentation_flow(surface, false_floor_y)
    
    def draw_sedimentation_flow(self, surface, false_floor_y):
        """Dibujar flujo de sedimentación y partículas"""
        
        # Flujo ascendente (velocidad ~0.25 mm/s)
        for i in range(10):
            flow_x = self.x + 20 + i * (self.width - 40) // 9
            
            # Líneas de flujo ascendente
            for j in range(3):
                flow_y_start = false_floor_y - j * 20
                flow_y_end = flow_y_start - 15
                
                # Animación sutil del flujo
                offset = int(time.time() * 20 + i * 10) % 20
                actual_y_start = flow_y_start + offset
                actual_y_end = flow_y_end + offset
                
                if actual_y_end > self.y + 20:
                    pygame.draw.line(surface, COLORS['water_clean'],
                                   (flow_x, actual_y_start), 
                                   (flow_x, actual_y_end), 1)
        
        # Partículas sedimentando (flóculos grandes caen)
        for i in range(5):
            # Verificar que el tanque sea lo suficientemente ancho
            if self.width > 60:
                particle_x = self.x + 30 + random.randint(0, self.width - 60)
            else:
                particle_x = self.x + self.width // 2
            
            # Animación de caída
            fall_speed = time.time() * 30 + i * 20
            particle_y = self.y + 30 + (fall_speed % (self.depth - 60))
            
            # Flóculos grandes (marrones)
            if particle_y > false_floor_y - 20:
                # Partículas sedimentadas en el fondo
                pygame.draw.circle(surface, COLORS['floc'], 
                                 (particle_x, false_floor_y + 5), 4)
            else:
                # Flóculos cayendo
                pygame.draw.circle(surface, COLORS['particle_large'], 
                                 (particle_x, int(particle_y)), 3)

class ControlPanel:
    """Panel de control interactivo mejorado"""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.coagulant_dose = 0.025
        self.flow_rate = 0.45  # L/s
        self.running = False
        self.simulation_speed = 1.0  # Velocidad de simulación (1x normal)
        self.buttons = {}
        self.sliders = {}
        
        # Parámetros configurables del agua de entrada
        self.initial_pH = 7.5
        self.initial_turbidity = 50.0  # NTU
        self.water_temperature = 20.0  # °C
        
        # Estado de la pestaña de configuración
        self.show_config = False  # Toggle para mostrar/ocultar configuraciones
        self.show_advanced_params = False  # Toggle para parámetros avanzados de calidad del agua
        
        # Parámetros editables de calidad del agua (entrada)
        self.water_quality_params = {
            'tss_entrada': 150.0,      # mg/L - Sólidos Suspendidos Totales
            'dqo_entrada': 180.0,      # mg/L - Demanda Química de Oxígeno
            'dbo_entrada': 90.0,       # mg/L - Demanda Biológica de Oxígeno
            'patogenos_entrada': 100000,  # CFU/mL - Patógenos (1x10^5)
            'oxigeno_disuelto': 7.5,   # mg/L - Oxígeno Disuelto
            'alcalinidad': 150.0,      # mg CaCO3/L - Alcalinidad
            'conductividad': 500.0     # μS/cm - Conductividad Eléctrica
        }
        
        # Campo de texto actualmente siendo editado
        self.editing_field = None
        self.editing_text = ""
        self.editable_fields = {}  # Inicializar diccionario de campos editables
        
        self.create_controls()
        
        # Parámetros hidráulicos calculados
        self.hydraulic_data = None
        self.update_hydraulic_data()
    
    def update_hydraulic_data(self):
        """Actualizar datos hidráulicos calculados"""
        try:
            # Calcular parámetros hidráulicos con el caudal actual
            Q = self.flow_rate / 1000  # m³/s
            mu = 1e-3  # Pa·s
            rho = 1000  # kg/m³
            
            # Mezcla rápida
            specs_rm = PILOT_PLANT_SPECS['rapid_mix']
            d_orifice = 0.021  # m
            A_orifice = np.pi * (d_orifice/2)**2
            v_jet = Q / A_orifice
            P_rm = 0.5 * rho * v_jet**2 * Q
            G_rm = np.sqrt(P_rm / (mu * specs_rm['volume']))
            
            # Floculación
            specs_floc = PILOT_PLANT_SPECS['flocculation']
            v_baffle = Q / (specs_floc['opening_free'] * specs_floc['water_height'])
            n_turns = specs_floc['n_baffles'] - 1
            h_loss = n_turns * 2.5 * v_baffle**2 / (2 * 9.81)
            P_floc = rho * 9.81 * Q * h_loss
            G_floc = np.sqrt(P_floc / (mu * specs_floc['volume']))
            
            # Sedimentación
            specs_sed = PILOT_PLANT_SPECS['sedimentation']
            v_upflow = Q / specs_sed['area']
            n_holes = specs_sed['false_floor']['total_holes']
            d_hole = specs_sed['false_floor']['hole_diameter']
            A_holes = n_holes * np.pi * (d_hole/2)**2
            v_holes = Q / A_holes
            SOR = Q * 3600 / specs_sed['area']
            
            self.hydraulic_data = {
                'rapid_mix': {
                    'velocity': v_jet,
                    'G': G_rm,
                    'power': P_rm,
                    'retention': specs_rm['volume'] / Q
                },
                'flocculation': {
                    'velocity': v_baffle,
                    'G': G_floc,
                    'head_loss': h_loss,
                    'power': P_floc,
                    'retention': specs_floc['volume'] / Q
                },
                'sedimentation': {
                    'upflow_velocity': v_upflow,
                    'hole_velocity': v_holes,
                    'SOR': SOR,
                    'retention': specs_sed['volume'] / Q
                }
            }
        except Exception as e:
            print(f"Error calculando datos hidráulicos: {e}")
            self.hydraulic_data = None
    
    def create_controls(self):
        """Crear controles interactivos organizados"""
        
        # Sección de control principal (adaptativa) - con espacio para el título
        control_y = self.y + int(45 * font_scale)
        
        # Botones principales en fila (adaptativos)
        button_width = int(80 * font_scale)
        button_height = int(35 * font_scale)
        button_spacing = int(10 * font_scale)
        
        self.buttons['start_stop'] = {
            'rect': pygame.Rect(self.x + 20, control_y, button_width, button_height),
            'text': 'INICIAR',
            'action': 'toggle_simulation',
            'color': COLORS['success']
        }
        
        self.buttons['pause'] = {
            'rect': pygame.Rect(self.x + 20 + button_width + button_spacing, control_y, button_width, button_height),
            'text': 'PAUSAR',
            'action': 'pause_simulation',
            'color': COLORS['warning']
        }
        
        self.buttons['reset'] = {
            'rect': pygame.Rect(self.x + 20 + 2*(button_width + button_spacing), control_y, button_width, button_height),
            'text': 'RESET',
            'action': 'reset_simulation',
            'color': COLORS['error']
        }
        
        self.buttons['exit'] = {
            'rect': pygame.Rect(self.x + 20 + 3*(button_width + button_spacing), control_y, button_width, button_height),
            'text': 'SALIR',
            'action': 'exit_program',
            'color': (100, 100, 100)
        }
        
        # Botón para mostrar/ocultar configuraciones (adaptativo, ancho completo)
        button_full_width = int(self.width - 40 * font_scale)
        self.buttons['config'] = {
            'rect': pygame.Rect(self.x + int(20 * font_scale), 
                              control_y + int(45 * font_scale), 
                              button_full_width, 
                              int(28 * font_scale)),
            'text': 'CONFIGURACIONES',
            'action': 'toggle_config',
            'color': (70, 100, 150)
        }
        
        # Botón para mostrar/ocultar parámetros avanzados (más ancho para el texto)
        button_full_width = int(self.width - 40 * font_scale)
        self.buttons['advanced'] = {
            'rect': pygame.Rect(self.x + int(20 * font_scale), 
                              control_y + int(80 * font_scale), 
                              button_full_width, 
                              int(28 * font_scale)),
            'text': 'PARAMETROS AVANZADOS',
            'action': 'toggle_advanced',
            'color': (100, 70, 150)
        }
        
        # Sliders organizados verticalmente (adaptativos) - ajustado para dar espacio al título
        slider_y = control_y + int(118 * font_scale)
        slider_height = int(20 * font_scale)
        slider_spacing = int(70 * font_scale)
        
        # Ancho de sliders adaptativo
        slider_width = int(min(300, self.width * 0.75))
        slider_margin = int(20 * font_scale)
        
        # Slider de velocidad de simulación
        self.sliders['simulation_speed'] = {
            'rect': pygame.Rect(self.x + slider_margin, slider_y, slider_width, slider_height),
            'min_val': 0.1,
            'max_val': 50.0,
            'current_val': self.simulation_speed,
            'label': 'Velocidad Simulacion',
            'format': '{:.1f}x',
            'logarithmic': True
        }
        
        # Slider de dosis de coagulante (ahora en relación proporcional: 10 por cada 4L)
        # La dosis se calcula automáticamente basada en el volumen
        # Relación: 10 unidades de coagulante por cada 4 litros de agua
        self.sliders['coagulant_dose'] = {
            'rect': pygame.Rect(self.x + slider_margin, slider_y + slider_spacing, slider_width, slider_height),
            'min_val': 0.005,
            'max_val': 0.060,
            'current_val': self.coagulant_dose,
            'label': 'Dosis Coagulante (relacion 10/4L)',
            'format': '{:.3f}',
            'note': 'Se calcula: 10 coagulante por cada 4L de agua'
        }
        
        # Slider de caudal
        self.sliders['flow_rate'] = {
            'rect': pygame.Rect(self.x + slider_margin, slider_y + 2*slider_spacing, slider_width, slider_height),
            'min_val': 0.30,
            'max_val': 0.60,
            'current_val': self.flow_rate,
            'label': 'Caudal (L/s)',
            'format': '{:.2f}'
        }
        
        # === SLIDERS DE CONFIGURACIÓN (se mostrarán solo si show_config = True) ===
        # Posicionar los sliders de configuración más arriba para mejor visibilidad
        config_slider_y = control_y + int(120 * font_scale)
        
        # Slider de pH inicial
        self.sliders['initial_pH'] = {
            'rect': pygame.Rect(self.x + slider_margin, config_slider_y, slider_width, slider_height),
            'min_val': 6.0,
            'max_val': 9.0,
            'current_val': self.initial_pH,
            'label': 'pH Inicial del Agua',
            'format': '{:.2f}',
            'is_config': True
        }
        
        # Slider de turbidez inicial
        self.sliders['initial_turbidity'] = {
            'rect': pygame.Rect(self.x + slider_margin, config_slider_y + slider_spacing, slider_width, slider_height),
            'min_val': 10.0,
            'max_val': 200.0,
            'current_val': self.initial_turbidity,
            'label': 'Turbidez Inicial (NTU)',
            'format': '{:.1f}',
            'is_config': True
        }
        
        # Slider de temperatura del agua
        self.sliders['water_temperature'] = {
            'rect': pygame.Rect(self.x + slider_margin, config_slider_y + 2*slider_spacing, slider_width, slider_height),
            'min_val': 5.0,
            'max_val': 35.0,
            'current_val': self.water_temperature,
            'label': 'Temperatura del Agua (C)',
            'format': '{:.1f}',
            'is_config': True
        }
    
    def handle_event(self, event):
        """Manejar eventos del panel de control"""
        
        # Manejar edición de texto en parámetros avanzados
        if self.show_advanced_params:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Verificar si se hizo clic en un campo editable
                clicked_field = None
                if hasattr(self, 'editable_fields'):
                    for field_name, field_rect in self.editable_fields.items():
                        if field_rect.collidepoint(mouse_pos):
                            clicked_field = field_name
                            break
                
                if clicked_field:
                    # Activar edición del campo
                    self.editing_field = clicked_field
                    current_value = self.water_quality_params[clicked_field]
                    if clicked_field == 'patogenos_entrada':
                        self.editing_text = f"{current_value:.0f}"
                    else:
                        self.editing_text = f"{current_value:.1f}"
                    print(f"🖱️ Editando campo: {clicked_field} = {self.editing_text}")
                    return None
                else:
                    # Clic fuera de campos, desactivar edición
                    if self.editing_field:
                        print(f"💾 Finalizando edición por clic fuera")
                        self.finish_editing()
            
            elif event.type == pygame.KEYDOWN and self.editing_field:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Confirmar edición
                    print(f"✅ Confirmando edición con Enter")
                    self.finish_editing()
                    return None
                elif event.key == pygame.K_ESCAPE:
                    # Cancelar edición
                    print(f"❌ Cancelando edición con Escape")
                    self.editing_field = None
                    self.editing_text = ""
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    # Borrar último carácter
                    self.editing_text = self.editing_text[:-1]
                    print(f"⌫ Texto actual: '{self.editing_text}'")
                    return None
                else:
                    # Añadir carácter si es válido (números y punto decimal)
                    if event.unicode.isdigit() or event.unicode == '.':
                        self.editing_text += event.unicode
                        print(f"📝 Texto actual: '{self.editing_text}'")
                    return None
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Verificar botones
            for button_name, button in self.buttons.items():
                if button['rect'].collidepoint(mouse_pos):
                    return button['action']
            
            # Verificar sliders
            for slider_name, slider in self.sliders.items():
                if slider['rect'].collidepoint(mouse_pos):
                    # Calcular nuevo valor del slider
                    relative_x = mouse_pos[0] - slider['rect'].x
                    ratio = relative_x / slider['rect'].width
                    ratio = max(0, min(1, ratio))
                    
                    new_val = slider['min_val'] + ratio * (slider['max_val'] - slider['min_val'])
                    slider['current_val'] = new_val
                    
                    if slider_name == 'coagulant':
                        self.coagulant_dose = new_val
                    elif slider_name == 'flow_rate':
                        self.flow_rate = new_val
        
        return None
    
    def finish_editing(self):
        """Finalizar la edición de un campo de texto"""
        if self.editing_field and self.editing_text:
            try:
                # Convertir texto a número
                new_value = float(self.editing_text)
                
                # Validar rangos según el parámetro
                if self.editing_field == 'tss_entrada':
                    new_value = max(10.0, min(500.0, new_value))
                elif self.editing_field == 'dqo_entrada':
                    new_value = max(50.0, min(1000.0, new_value))
                elif self.editing_field == 'dbo_entrada':
                    new_value = max(20.0, min(500.0, new_value))
                elif self.editing_field == 'patogenos_entrada':
                    new_value = max(1000.0, min(1000000.0, new_value))
                elif self.editing_field == 'oxigeno_disuelto':
                    new_value = max(0.0, min(15.0, new_value))
                elif self.editing_field == 'alcalinidad':
                    new_value = max(50.0, min(500.0, new_value))
                elif self.editing_field == 'conductividad':
                    new_value = max(100.0, min(2000.0, new_value))
                
                # Actualizar valor
                self.water_quality_params[self.editing_field] = new_value
                print(f"💧 {self.editing_field} actualizado a {new_value}")
                
            except ValueError:
                print(f"❌ Valor inválido para {self.editing_field}: {self.editing_text}")
        
        # Limpiar estado de edición
        self.editing_field = None
        self.editing_text = ""
    
    def draw(self, surface):
        """Dibujar panel de control mejorado"""
        # Fondo del panel con gradiente
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (25, 35, 50), panel_rect)
        pygame.draw.rect(surface, COLORS['tank_border'], panel_rect, 3)
        
        # Título del panel (más visible y con más espacio)
        title = font_large.render("PANEL DE CONTROL", True, COLORS['text'])
        title_rect = title.get_rect(centerx=self.x + self.width//2, y=self.y + 8)
        surface.blit(title, title_rect)
        
        # Línea separadora (con más espacio después del título)
        pygame.draw.line(surface, COLORS['tank_border'], 
                        (self.x + 10, self.y + 40), 
                        (self.x + self.width - 10, self.y + 40), 2)
        
        # Dibujar botones con mejor estilo
        for button_name, button in self.buttons.items():
            self.draw_modern_button(surface, button_name, button)
        
        # Dibujar sliders dependiendo del modo activo
        for slider_name, slider in self.sliders.items():
            is_config_slider = slider.get('is_config', False)
            
            if self.show_config:
                # En modo configuración: solo mostrar sliders de configuración
                if is_config_slider:
                    self.draw_modern_slider(surface, slider_name, slider)
            elif self.show_advanced_params:
                # En modo parámetros avanzados: no mostrar sliders (solo info)
                pass
            else:
                # En modo normal: solo mostrar sliders normales (no-config)
                if not is_config_slider:
                    self.draw_modern_slider(surface, slider_name, slider)
        
        # Dibujar secciones según el modo activo
        if self.show_config:
            # Título para los sliders de configuración (posicionado mejor)
            sliders_title_y = self.y + int(self.height * 0.42)
            sliders_title = font_small.render("AJUSTAR PARÁMETROS CON LOS SLIDERS:", True, (100, 200, 255))
            surface.blit(sliders_title, (self.x + int(20 * font_scale), sliders_title_y))
            
            # Línea separadora debajo del título de sliders
            pygame.draw.line(surface, (100, 200, 255), 
                            (self.x + 20, sliders_title_y + 18), 
                            (self.x + self.width - 20, sliders_title_y + 18), 1)
            
            self.draw_config_section(surface)
        elif self.show_advanced_params:
            print("Dibujando parametros avanzados...")  # DEBUG
            self.draw_advanced_parameters_section(surface)
        else:
            # Información del sistema organizada (solo en modo normal)
            self.draw_organized_info(surface)
            # Panel de datos hidráulicos reales
            self.draw_hydraulic_data_panel(surface)
    
    def draw_modern_button(self, surface, button_name, button):
        """Dibujar botón con estilo moderno"""
        # Determinar color según estado
        if button_name == 'start_stop' and self.running:
            color = COLORS['success']
            text_color = (255, 255, 255)
        elif button_name == 'exit':
            color = (150, 50, 50)
            text_color = (255, 255, 255)
        elif button_name == 'config' and self.show_config:
            color = (100, 150, 200)  # Color diferente cuando está activo
            text_color = (255, 255, 255)
        elif button_name == 'advanced' and self.show_advanced_params:
            color = (150, 100, 200)  # Color diferente cuando está activo
            text_color = (255, 255, 255)
        else:
            color = button.get('color', COLORS['button'])
            text_color = (255, 255, 255)
        
        # Efecto hover
        mouse_pos = pygame.mouse.get_pos()
        if button['rect'].collidepoint(mouse_pos):
            color = tuple(min(255, c + 30) for c in color)
        
        # Dibujar botón con bordes redondeados (simulado)
        pygame.draw.rect(surface, color, button['rect'])
        pygame.draw.rect(surface, (200, 200, 200), button['rect'], 2)
        
        # Texto centrado
        text = button['text']
        if button_name == 'start_stop' and self.running:
            text = 'DETENER'
        elif button_name == 'config':
            text = 'CONFIGURACIONES ▼' if not self.show_config else 'CONFIGURACIONES ▲'
        elif button_name == 'advanced':
            text = 'PARAMETROS AVANZADOS ▼' if not self.show_advanced_params else 'PARAMETROS AVANZADOS ▲'
        
        # Ajustar tamaño de fuente si el texto es muy largo
        if len(text) > 20:
            text_surface = font_small.render(text, True, text_color)
        else:
            text_surface = font_small.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=button['rect'].center)
        surface.blit(text_surface, text_rect)
    
    
    def draw_modern_slider(self, surface, slider_name, slider):
        """Dibujar slider con estilo moderno"""
        # Etiqueta del slider
        label_y = slider['rect'].y - 25
        label_text = font_small.render(slider['label'], True, COLORS['text'])
        surface.blit(label_text, (slider['rect'].x, label_y))
        
        # Valor actual
        current_val = slider['current_val']
        value_text = slider['format'].format(current_val)
        
        # Color especial para el slider de velocidad
        if slider_name == 'simulation_speed':
            if current_val >= 10:
                value_color = (255, 100, 100)  # Rojo para velocidades altas
            elif current_val >= 5:
                value_color = (255, 165, 0)  # Naranja
            else:
                value_color = (100, 255, 100)  # Verde para velocidades normales
        else:
            value_color = COLORS['text']
        
        value_surface = font_small.render(f"Valor: {value_text}", True, value_color)
        surface.blit(value_surface, (slider['rect'].x + 200, label_y))
        
        # Barra del slider
        track_rect = pygame.Rect(slider['rect'].x, slider['rect'].y + 5, slider['rect'].width, 10)
        pygame.draw.rect(surface, (60, 60, 60), track_rect)
        pygame.draw.rect(surface, COLORS['tank_border'], track_rect, 1)
        
        # Handle del slider
        min_val = slider['min_val']
        max_val = slider['max_val']
        
        # Si es logarítmico, usar escala logarítmica
        if slider.get('logarithmic', False):
            # Convertir a escala logarítmica
            log_min = np.log10(min_val)
            log_max = np.log10(max_val)
            log_current = np.log10(current_val)
            ratio = (log_current - log_min) / (log_max - log_min)
        else:
            ratio = (current_val - min_val) / (max_val - min_val)
        
        handle_pos = slider['rect'].x + int(ratio * slider['rect'].width)
        handle_rect = pygame.Rect(handle_pos - 8, slider['rect'].y, 16, 20)
        
        # Color del handle según el slider
        if slider_name == 'simulation_speed':
            handle_color = value_color
        else:
            handle_color = COLORS['button']
        
        pygame.draw.rect(surface, handle_color, handle_rect)
        pygame.draw.rect(surface, (255, 255, 255), handle_rect, 2)
    
    def draw_hydraulic_data_panel(self, surface):
        """Dibujar panel con datos hidráulicos reales calculados"""
        if not self.hydraulic_data:
            return
        
        panel_y = self.y + int(self.height * 0.72)  # Posición del panel (72% de la altura)
        panel_height = int(self.height * 0.25)  # 25% de la altura del panel
        
        # Fondo del panel
        panel_rect = pygame.Rect(self.x + 10, panel_y, self.width - 20, panel_height)
        pygame.draw.rect(surface, (30, 40, 55), panel_rect)
        pygame.draw.rect(surface, COLORS['tank_border'], panel_rect, 2)
        
        # Título compacto
        title = font_small.render("DATOS HIDRAULICOS CALCULADOS", True, (100, 255, 100))
        surface.blit(title, (panel_rect.x + int(10 * font_scale), panel_rect.y + int(5 * font_scale)))
        
        # Datos de mezcla rápida
        rm_data = self.hydraulic_data['rapid_mix']
        rm_text = [
            "MEZCLA RÁPIDA:",
            f"  Velocidad chorro: {rm_data['velocity']:.2f} m/s",
            f"  Gradiente G: {rm_data['G']:.0f} s⁻¹",
            f"  Potencia disipada: {rm_data['power']:.3f} W",
            f"  Tiempo retención: {rm_data['retention']:.1f} s"
        ]
        
        # Datos de floculación
        floc_data = self.hydraulic_data['flocculation']
        floc_text = [
            "FLOCULACIÓN:",
            f"  Velocidad bafles: {floc_data['velocity']:.3f} m/s",
            f"  Gradiente G: {floc_data['G']:.0f} s⁻¹",
            f"  Pérdida carga: {floc_data['head_loss']*1000:.1f} mm",
            f"  Potencia: {floc_data['power']:.3f} W",
            f"  Tiempo retención: {floc_data['retention']:.1f} s"
        ]
        
        # Datos de sedimentación
        sed_data = self.hydraulic_data['sedimentation']
        sed_text = [
            "SEDIMENTACIÓN:",
            f"  Velocidad ascensional: {sed_data['upflow_velocity']*1000:.2f} mm/s",
            f"  Velocidad orificios: {sed_data['hole_velocity']:.3f} m/s",
            f"  Tasa carga (SOR): {sed_data['SOR']:.2f} m/h",
            f"  Tiempo retención: {sed_data['retention']:.0f} s"
        ]
        
        # Dibujar en columnas
        col1_x = panel_rect.x + 10
        col2_x = panel_rect.x + 250
        col3_x = panel_rect.x + 490
        text_y = panel_rect.y + 35
        
        for i, line in enumerate(rm_text):
            color = (150, 200, 255) if i == 0 else COLORS['text']
            text_surface = font_small.render(line, True, color)
            surface.blit(text_surface, (col1_x, text_y + i * 16))
        
        for i, line in enumerate(floc_text):
            color = (150, 200, 255) if i == 0 else COLORS['text']
            text_surface = font_small.render(line, True, color)
            surface.blit(text_surface, (col2_x, text_y + i * 16))
        
        for i, line in enumerate(sed_text):
            color = (150, 200, 255) if i == 0 else COLORS['text']
            text_surface = font_small.render(line, True, color)
            surface.blit(text_surface, (col3_x, text_y + i * 16))
        
        # Información del caudal actual
        flow_text = f"Caudal operativo: {self.flow_rate:.2f} L/s ({self.flow_rate*3600:.1f} L/h)"
        flow_surface = font_small.render(flow_text, True, (255, 200, 100))
        surface.blit(flow_surface, (panel_rect.x + 10, panel_rect.y + panel_height - 20))
    
    def draw_config_section(self, surface):
        """Dibujar sección de configuración mejorada con mejor diseño"""
        # Posicionar la sección más abajo para dejar espacio a los sliders
        config_y = self.y + int(self.height * 0.65)
        
        # Fondo de la sección de configuración (más pequeño para dejar espacio a sliders)
        section_rect = pygame.Rect(self.x + 10, config_y - 5, self.width - 20, int(self.height * 0.30))
        pygame.draw.rect(surface, (30, 45, 65), section_rect)  # Fondo azul oscuro
        pygame.draw.rect(surface, (100, 200, 255), section_rect, 2)  # Borde azul
        
        # Título de la sección con mejor formato
        config_title = font_medium.render("CONFIGURACIÓN DEL AGUA DE ENTRADA", True, (100, 200, 255))
        title_rect = config_title.get_rect(centerx=self.x + self.width//2, y=config_y)
        surface.blit(config_title, title_rect)
        
        # Línea separadora debajo del título
        pygame.draw.line(surface, (100, 200, 255), 
                        (self.x + 20, config_y + 25), 
                        (self.x + self.width - 20, config_y + 25), 1)
        
        # Información organizada en secciones
        content_y = config_y + 35
        line_h = int(18 * font_scale)
        
        # Sección de parámetros actuales
        params_title = font_small.render("PARÁMETROS ACTUALES:", True, (150, 220, 255))
        surface.blit(params_title, (self.x + int(20 * font_scale), content_y))
        content_y += line_h + 5
        
        # Parámetros con mejor formato y colores
        params_info = [
            ("pH Inicial:", f"{self.initial_pH:.2f}", "(Rango: 6.0 - 9.0)", (150, 200, 255), (200, 255, 200), (180, 180, 180)),
            ("Turbidez:", f"{self.initial_turbidity:.0f} NTU", "(Rango: 10 - 200)", (150, 200, 255), (200, 255, 200), (180, 180, 180)),
            ("Temperatura:", f"{self.water_temperature:.0f} °C", "(Rango: 5 - 35)", (150, 200, 255), (200, 255, 200), (180, 180, 180))
        ]
        
        for param_name, value, range_text, color1, color2, color3 in params_info:
            # Nombre del parámetro
            param_surface = font_small.render(param_name, True, color1)
            surface.blit(param_surface, (self.x + int(25 * font_scale), content_y))
            
            # Valor actual
            value_surface = font_small.render(value, True, color2)
            surface.blit(value_surface, (self.x + int(120 * font_scale), content_y))
            
            # Rango permitido
            range_surface = font_small.render(range_text, True, color3)
            surface.blit(range_surface, (self.x + int(200 * font_scale), content_y))
            
            content_y += line_h
        
        # Espacio adicional
        content_y += 10
        
        # Sección de instrucciones
        instructions_title = font_small.render("INSTRUCCIONES:", True, (255, 200, 100))
        surface.blit(instructions_title, (self.x + int(20 * font_scale), content_y))
        content_y += line_h + 3
        
        instructions = [
            "• Use los sliders arriba para ajustar valores",
            "• Los cambios se aplican inmediatamente",
            "• Presione RESET para aplicar nuevos valores",
            "• Los valores afectan la simulación completa"
        ]
        
        for instruction in instructions:
            inst_surface = font_small.render(instruction, True, (200, 200, 200))
            surface.blit(inst_surface, (self.x + int(25 * font_scale), content_y))
            content_y += line_h - 2
        
        # Advertencia importante
        content_y += 8
        warning_bg = pygame.Rect(self.x + 15, content_y - 3, self.width - 30, 25)
        pygame.draw.rect(surface, (80, 60, 20), warning_bg)
        pygame.draw.rect(surface, (255, 200, 100), warning_bg, 1)
        
        warning_text = font_small.render("⚠ IMPORTANTE: Presione RESET después de cambiar parámetros", True, (255, 200, 100))
        warning_rect = warning_text.get_rect(centerx=self.x + self.width//2, y=content_y)
        surface.blit(warning_text, warning_rect)
    
    def draw_advanced_parameters_section(self, surface):
        """Dibujar sección compacta de parámetros avanzados editables"""
        
        # Posición que no tape los botones
        params_y = self.y + int(self.height * 0.35)
        
        # Fondo compacto que no se salga de la pantalla
        section_height = int(self.height * 0.60)  # Más pequeño
        section_rect = pygame.Rect(self.x + 10, params_y - 5, self.width - 20, section_height)
        pygame.draw.rect(surface, (25, 35, 55), section_rect)
        pygame.draw.rect(surface, (100, 150, 255), section_rect, 2)
        
        # Título compacto
        title = font_small.render("PARÁMETROS DE CALIDAD DEL AGUA", True, (100, 150, 255))
        title_rect = title.get_rect(centerx=self.x + self.width//2, y=params_y)
        surface.blit(title, title_rect)
        
        # Instrucción compacta
        instruction = font_small.render("Clic en valores para editar", True, (150, 200, 255))
        instruction_rect = instruction.get_rect(centerx=self.x + self.width//2, y=params_y + 18)
        surface.blit(instruction, instruction_rect)
        
        current_y = params_y + 40
        line_h = int(16 * font_scale)  # Líneas más compactas
        
        # === PARÁMETROS EDITABLES EN FORMATO COMPACTO ===
        # Entrada
        entrada_title = font_small.render("ENTRADA:", True, (255, 200, 100))
        surface.blit(entrada_title, (self.x + 15, current_y))
        current_y += line_h + 2
        
        # Parámetros de entrada en formato compacto
        entrada_params = [
            ('tss_entrada', 'TSS:', 'mg/L'),
            ('dqo_entrada', 'DQO:', 'mg/L'),
            ('dbo_entrada', 'DBO:', 'mg/L'),
            ('patogenos_entrada', 'Patógenos:', 'CFU/mL')
        ]
        
        for param_key, label, unit in entrada_params:
            current_y = self.draw_compact_editable_field(surface, param_key, label, unit, current_y)
        
        current_y += 8
        
        # Otros parámetros
        otros_title = font_small.render("OTROS:", True, (255, 200, 100))
        surface.blit(otros_title, (self.x + 15, current_y))
        current_y += line_h + 2
        
        otros_params = [
            ('oxigeno_disuelto', 'O₂ Disuelto:', 'mg/L'),
            ('alcalinidad', 'Alcalinidad:', 'mg/L'),
            ('conductividad', 'Conductividad:', 'μS/cm')
        ]
        
        for param_key, label, unit in otros_params:
            current_y = self.draw_compact_editable_field(surface, param_key, label, unit, current_y)
        
        current_y += 8
        
        # === VALORES CALCULADOS (SOLO LECTURA) ===
        calc_title = font_small.render("SALIDA CALCULADA:", True, (100, 255, 100))
        surface.blit(calc_title, (self.x + 15, current_y))
        current_y += line_h + 2
        
        # Calcular y mostrar valores de salida
        tss_out = self.water_quality_params['tss_entrada'] * 0.10
        dqo_out = self.water_quality_params['dqo_entrada'] * 0.40
        
        calc_params = [
            f"TSS: {tss_out:.1f} mg/L (90% rem.)",
            f"DQO: {dqo_out:.1f} mg/L (60% rem.)",
            f"Turbidez: <5 NTU (90% rem.)"
        ]
        
        for calc_text in calc_params:
            calc_surface = font_small.render(calc_text, True, (200, 255, 200))
            surface.blit(calc_surface, (self.x + 20, current_y))
            current_y += line_h - 2
        
        # Nota final compacta
        current_y += 5
        note = font_small.render("💡 Valores típicos agua cruda", True, (180, 180, 180))
        note_rect = note.get_rect(centerx=self.x + self.width//2, y=current_y)
        surface.blit(note, note_rect)
    
    def draw_compact_editable_field(self, surface, param_key, label, unit, y):
        """Dibujar campo editable compacto"""
        
        # Etiqueta
        label_surface = font_small.render(label, True, (150, 200, 255))
        surface.blit(label_surface, (self.x + 20, y))
        
        # Valor actual
        value = self.water_quality_params[param_key]
        if param_key == 'patogenos_entrada':
            value_text = f"{value:.0f}"
        else:
            value_text = f"{value:.1f}"
        
        # Campo de texto compacto
        field_x = self.x + 120
        field_width = 60
        field_height = 16
        field_rect = pygame.Rect(field_x, y - 1, field_width, field_height)
        
        # Estilo del campo
        if self.editing_field == param_key:
            # Campo activo
            pygame.draw.rect(surface, (60, 100, 160), field_rect)
            pygame.draw.rect(surface, (100, 200, 255), field_rect, 2)
            display_text = self.editing_text + "|"
            text_color = (255, 255, 255)
        else:
            # Campo inactivo - clickeable
            mouse_pos = pygame.mouse.get_pos()
            if field_rect.collidepoint(mouse_pos):
                # Hover effect
                pygame.draw.rect(surface, (50, 70, 100), field_rect)
                pygame.draw.rect(surface, (150, 180, 255), field_rect, 1)
            else:
                pygame.draw.rect(surface, (40, 50, 70), field_rect)
                pygame.draw.rect(surface, (100, 120, 180), field_rect, 1)
            display_text = value_text
            text_color = (200, 255, 200)
        
        # Texto del valor
        value_surface = font_small.render(display_text, True, text_color)
        value_rect = value_surface.get_rect(center=(field_x + field_width//2, y + 7))
        surface.blit(value_surface, value_rect)
        
        # Unidad
        unit_surface = font_small.render(unit, True, (180, 180, 180))
        surface.blit(unit_surface, (field_x + field_width + 5, y))
        
        # Guardar rect para detección de clics
        if not hasattr(self, 'editable_fields'):
            self.editable_fields = {}
        self.editable_fields[param_key] = field_rect
        
        return y + int(18 * font_scale)  # Espaciado más compacto
    
    def draw_editable_parameter(self, surface, param_key, param_name, unit, x, y, color):
        """Dibujar un parámetro editable con campo de texto"""
        
        # Nombre del parámetro
        name_surface = font_small.render(f"{param_name}:", True, color)
        surface.blit(name_surface, (x, y))
        
        # Campo de valor editable
        value = self.water_quality_params[param_key]
        
        # Formatear valor según el tipo
        if param_key == 'patogenos_entrada':
            value_text = f"{value:.0f}"
        else:
            value_text = f"{value:.1f}"
        
        # Área del campo de texto
        field_x = x + 280
        field_width = 80
        field_height = 18
        field_rect = pygame.Rect(field_x, y - 2, field_width, field_height)
        
        # Color del campo según si está siendo editado
        if self.editing_field == param_key:
            # Campo activo (siendo editado)
            pygame.draw.rect(surface, (80, 120, 200), field_rect)
            pygame.draw.rect(surface, (150, 200, 255), field_rect, 2)
            display_text = self.editing_text + "|"  # Cursor
            text_color = (255, 255, 255)
        else:
            # Campo inactivo
            pygame.draw.rect(surface, (60, 60, 80), field_rect)
            pygame.draw.rect(surface, (120, 120, 140), field_rect, 1)
            display_text = value_text
            text_color = (200, 255, 200)
        
        # Texto del valor
        value_surface = font_small.render(display_text, True, text_color)
        value_rect = value_surface.get_rect(center=(field_x + field_width//2, y + 7))
        surface.blit(value_surface, value_rect)
        
        # Unidad
        unit_surface = font_small.render(unit, True, (180, 180, 180))
        surface.blit(unit_surface, (field_x + field_width + 5, y))
        
        # Guardar rect para detección de clics
        if not hasattr(self, 'editable_fields'):
            self.editable_fields = {}
        self.editable_fields[param_key] = field_rect
        
        return y + int(20 * font_scale)
    
    def draw_organized_info(self, surface):
        """Dibujar información del sistema de forma organizada"""
        info_y = self.y + int(self.height * 0.48)  # Proporcional
        
        # Sección de especificaciones
        spec_title = font_medium.render("ESPECIFICACIONES REALES:", True, (100, 255, 100))
        surface.blit(spec_title, (self.x + 20, info_y))
        
        # Especificaciones más compactas en 3 columnas
        col_width = int(self.width * 0.32)
        col1_x = self.x + int(15 * font_scale)
        col2_x = col1_x + col_width
        col3_x = col2_x + col_width
        text_y = info_y + int(30 * font_scale)
        line_h = int(15 * font_scale)
        
        # Columna 1 - CAJA 1
        # Volumen real: 23×23×23 cm (altura útil) = 12.167 L
        specs1 = [
            "CAJA 1 - M.RAPIDA:",
            "23x23x24 cm",
            "Vol: 12.2 L",
            "G: calculado"
        ]
        for i, text in enumerate(specs1):
            color = (150, 200, 255) if i == 0 else (180, 180, 180)
            surf = font_small.render(text, True, color)
            surface.blit(surf, (col1_x, text_y + i * line_h))
        
        # Columna 2 - CAJA 2
        # Volumen real: 30×14×23 cm (altura útil) = 9.66 L
        specs2 = [
            "CAJA 2 - FLOCULACION:",
            "30x14x24 cm",
            "Vol: 9.7 L",
            "G: calculado"
        ]
        for i, text in enumerate(specs2):
            color = (150, 200, 255) if i == 0 else (180, 180, 180)
            surf = font_small.render(text, True, color)
            surface.blit(surf, (col2_x, text_y + i * line_h))
        
        # Columna 3 - CAJA 3
        # Volumen real: 30×14×23 cm (altura útil) = 9.66 L
        specs3 = [
            "CAJA 3 - SEDIMENTACION:",
            "30x14x24 cm",
            "Vol: 9.7 L",
            "55 orif. O2mm"
        ]
        for i, text in enumerate(specs3):
            color = (150, 200, 255) if i == 0 else (180, 180, 180)
            surf = font_small.render(text, True, color)
            surface.blit(surf, (col3_x, text_y + i * line_h))
        
        # Parámetros operativos abajo
        params_y = text_y + int(70 * font_scale)
        param_title = font_small.render("PARAMETROS OPERATIVOS:", True, (255, 200, 100))
        surface.blit(param_title, (col1_x, params_y))
        
        # Calcular tiempo total de retención con volúmenes reales
        total_vol = 12.2 + 9.7 + 9.7  # L
        total_time = total_vol / 0.45  # s (con caudal típico)
        param_text = f"Caudal: 0.45 L/s  |  Tiempo total: ~{total_time:.0f} s"
        param_surf = font_small.render(param_text, True, (180, 180, 180))
        surface.blit(param_surf, (col1_x, params_y + line_h))
    
    def handle_event(self, event):
        """Manejar eventos del panel de control"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Verificar botones
            for button_name, button in self.buttons.items():
                if button['rect'].collidepoint(mouse_pos):
                    return button['action']
            
            # Verificar sliders
            for slider_name, slider in self.sliders.items():
                if slider['rect'].collidepoint(mouse_pos):
                    # Calcular nuevo valor del slider
                    relative_x = mouse_pos[0] - slider['rect'].x
                    ratio = relative_x / slider['rect'].width
                    ratio = max(0, min(1, ratio))
                    
                    # Si es logarítmico, convertir de escala logarítmica
                    if slider.get('logarithmic', False):
                        log_min = np.log10(slider['min_val'])
                        log_max = np.log10(slider['max_val'])
                        log_val = log_min + ratio * (log_max - log_min)
                        new_val = 10 ** log_val
                    else:
                     new_val = slider['min_val'] + ratio * (slider['max_val'] - slider['min_val'])
                    
                    slider['current_val'] = new_val
                    
                    if slider_name == 'simulation_speed':
                        self.simulation_speed = new_val
                        print(f"⚡ Velocidad ajustada a {new_val:.1f}x")
                    elif slider_name == 'coagulant_dose':
                        self.coagulant_dose = new_val
                    elif slider_name == 'flow_rate':
                        self.flow_rate = new_val
                        # Actualizar datos hidráulicos cuando cambia el caudal
                        self.update_hydraulic_data()
                    elif slider_name == 'initial_pH':
                        self.initial_pH = new_val
                        print(f"🌊 pH inicial ajustado a {new_val:.2f} (reiniciar simulación)")
                    elif slider_name == 'initial_turbidity':
                        self.initial_turbidity = new_val
                        print(f"🌊 Turbidez inicial ajustada a {new_val:.1f} NTU (reiniciar simulación)")
                    elif slider_name == 'water_temperature':
                        self.water_temperature = new_val
                        print(f"🌡 Temperatura ajustada a {new_val:.1f} °C (reiniciar simulación)")
        
        # Verificar si se hizo clic en botones especiales (configuración y parámetros avanzados)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button_name, button in self.buttons.items():
                if button['rect'].collidepoint(mouse_pos):
                    if button['action'] == 'toggle_config':
                        self.show_config = not self.show_config
                        # Si activamos config, desactivar advanced
                        if self.show_config:
                            self.show_advanced_params = False
                        print(f"Config toggled: {self.show_config}")
                        return 'toggle_config'
                    elif button['action'] == 'toggle_advanced':
                        self.show_advanced_params = not self.show_advanced_params
                        # Si activamos advanced, desactivar config
                        if self.show_advanced_params:
                            self.show_config = False
                        print(f"PARAMETROS AVANZADOS toggled: {self.show_advanced_params}")
                        return 'toggle_advanced'
        
        return None
    
    def set_simulation_speed(self, speed):
        """Establecer la velocidad de simulación"""
        self.simulation_speed = speed
        print(f"⚡ Velocidad de simulación cambiada a {speed}x")
        
        # Mensaje visual para el usuario
        if speed == 1.0:
            print("   ⏸️ Velocidad NORMAL (tiempo real)")
        elif speed == 2.0:
            print("   ⏩ Velocidad DOBLE")
        elif speed == 5.0:
            print("   ⏩⏩ Velocidad 5X")
        elif speed == 10.0:
            print("   ⏩⏩⏩ Velocidad 10X")
        elif speed >= 50.0:
            print("   🚀 Velocidad MÁXIMA")

class WaterTreatmentGame:
    """Clase principal del juego/simulador"""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        self.simulation_running = False
        
        # Crear tanques con dimensiones reales organizados horizontalmente
        # Escala adaptativa según el tamaño del área principal (más pequeña para que quepa todo)
        scale = min(MAIN_AREA.width / 900, MAIN_AREA.height / 500) * 8
        
        # Disposición horizontal adaptativa - más abajo para dar espacio a las etiquetas
        tank_spacing = int(MAIN_AREA.width * 0.29)  # 29% del ancho
        base_x = MAIN_AREA.x + int(MAIN_AREA.width * 0.03)
        base_y = MAIN_AREA.y + int(MAIN_AREA.height * 0.55)  # Más abajo (55% en lugar de 45%)
        
        self.tanks = [
            # Caja 1 - Mezcla Rápida: 23×23×24 cm (ancho×largo×alto)
            Tank(base_x, base_y, 0.23, 0.23, 0.24, 'rapid_mix', 'CAJA 1 - MEZCLA RÁPIDA', scale),
            
            # Caja 2 - Floculación: 30×14×24 cm (ancho×largo×alto)
            Tank(base_x + tank_spacing, base_y, 0.30, 0.14, 0.24, 'flocculation', 'CAJA 2 - FLOCULACIÓN', scale),
            
            # Caja 3 - Sedimentación: 30×14×24 cm (ancho×largo×alto)
            Tank(base_x + 2*tank_spacing, base_y + 20, 0.30, 0.14, 0.24, 'sedimentation', 'CAJA 3 - SEDIMENTACIÓN', scale)
        ]
        
        # Panel de control usando el nuevo layout
        self.control_panel = ControlPanel(CONTROL_PANEL.x, CONTROL_PANEL.y, CONTROL_PANEL.width, CONTROL_PANEL.height)
        
        # Sistema de flujo
        self.water_flow = WaterFlow()
        
        # Simulación científica
        self.pilot_sim = PilotPlantSimulation()
        self.pilot_sim.setup_pilot_system()
        
        # Partículas y animación
        self.particles = []
        self.simulation_time = 0
        self.last_particle_spawn = 0
        
        # Sistema de gráficas y registro de datos
        self.data_logger = PlantDataLogger()
        self.graph_generator = PlantGraphGenerator()
        
        # Resultados de simulación
        self.simulation_results = None
        self.simulation_progress = 0.0  # Progreso de 0 a 1
        
        # Estado del agua en cada tanque (dinámico) - usa valores configurables
        initial_turbidity = self.control_panel.initial_turbidity
        initial_pH = self.control_panel.initial_pH
        
        self.water_state = {
            'rapid_mix': {
                'turbidity': initial_turbidity,
                'pH': initial_pH,
                'color_turbidity': initial_turbidity,
                'particles_removed': 0.0
            },
            'flocculation': {
                'turbidity': initial_turbidity,
                'pH': initial_pH,
                'color_turbidity': initial_turbidity,
                'particles_removed': 0.0
            },
            'sedimentation': {
                'turbidity': initial_turbidity,
                'pH': initial_pH,
                'color_turbidity': initial_turbidity,
                'particles_removed': 0.0
            }
        }
        
        # Actualizar parámetros hidráulicos de los tanques con el caudal inicial
        self.update_tanks_hydraulics()
        
        # Variables para gráficas
        self.show_graphs = False
        self.graphs_surface = None
        self.last_data_log = 0
        self.data_log_interval = 5.0  # Registrar datos cada 5 segundos
    
    def update_tanks_hydraulics(self):
        """Actualizar parámetros hidráulicos de todos los tanques"""
        for tank in self.tanks:
            tank.update_hydraulic_parameters(self.control_panel.flow_rate)
    
    def calculate_coagulant_dose(self):
        """Calcular dosis de coagulante basada en el volumen REAL del tanque
        Relación: 10 unidades de coagulante por cada 4 litros de agua
        
        Dimensiones reales Caja 1: 23×23×24 cm
        Volumen real = 23 × 23 × 24 = 12,696 cm³ = 12.696 L
        (Asumiendo altura útil de agua ~23 cm, volumen útil ≈ 12.2 L)
        """
        # Obtener el tanque de mezcla rápida
        rapid_mix_tank = self.tanks[0]
        
        # Calcular volumen REAL del tanque (dimensiones reales: 23×23×24 cm)
        # Usar altura útil de agua (aproximadamente 23 cm de los 24 cm totales)
        length_cm = 23  # cm
        width_cm = 23   # cm
        water_height_cm = 23  # cm (altura útil de agua)
        
        volume_liters = (length_cm * width_cm * water_height_cm) / 1000.0  # L
        
        # Relación: 10 de coagulante por cada 4 litros de agua
        # Esto es la cantidad TOTAL de coagulante para el volumen del tanque
        coagulant_dose = (volume_liters / 4.0) * 10
        
        return coagulant_dose
    
    def update_tank_colors(self):
        """Actualizar colores de los tanques según el estado del agua"""
        # Caja 1 - Mezcla Rápida
        self.tanks[0].current_turbidity = self.water_state['rapid_mix']['color_turbidity']
        
        # Calcular y mostrar dosis de coagulante en mezcla rápida
        coagulant_dose = self.calculate_coagulant_dose()
        self.tanks[0].coagulant_dose_display = coagulant_dose
        
        # Caja 2 - Floculación
        self.tanks[1].current_turbidity = self.water_state['flocculation']['color_turbidity']
        
        # Caja 3 - Sedimentación
        self.tanks[2].current_turbidity = self.water_state['sedimentation']['color_turbidity']
        
    def spawn_particles(self):
        """Generar nuevas partículas en la entrada"""
        current_time = time.time()
        # Intervalo de generación depende de la velocidad de simulación
        spawn_interval = 0.1 / max(1.0, self.control_panel.simulation_speed / 2)
        
        if current_time - self.last_particle_spawn > spawn_interval:
            # Añadir más partículas si la velocidad es alta
            n_particles = min(10, int(3 * self.control_panel.simulation_speed))
            for _ in range(n_particles):
                x = 50
                y = self.tanks[0].y + self.tanks[0].depth // 2 + random.randint(-20, 20)
                size = np.random.lognormal(0, 1)
                particle = Particle(x, y, size)
                self.particles.append(particle)
            
            self.last_particle_spawn = current_time
    
    def update_particles(self, dt):
        """Actualizar todas las partículas"""
        particles_to_remove = []
        
        for particle in self.particles:
            # Determinar en qué tanque está la partícula
            current_tank = None
            for tank in self.tanks:
                bounds = tank.get_bounds()
                if (bounds[0] <= particle.x <= bounds[2] and 
                    bounds[1] <= particle.y <= bounds[3]):
                    current_tank = tank
                    break
            
            if current_tank:
                # Actualizar campo de flujo
                self.water_flow.update_flow_field(current_tank.tank_type, current_tank.get_bounds())
                
                # Aplicar procesos específicos
                if current_tank.tank_type == 'rapid_mix':
                    if random.random() < self.control_panel.coagulant_dose * 5:
                        particle.coagulated = True
                        particle.size *= 1.1
                
                elif current_tank.tank_type == 'flocculation':
                    if particle.coagulated and random.random() < 0.02:
                        particle.flocculated = True
                        particle.size *= 2
                
                elif current_tank.tank_type == 'sedimentation':
                    if particle.flocculated:
                        particle.velocity_y += particle.size * 0.05  # Sedimentación
            
            # Actualizar posición
            particle.update(dt, self.water_flow.flow_vectors)
            
            # Remover partículas que salen del sistema
            if particle.x > 800 or particle.y > 400:
                particles_to_remove.append(particle)
        
        # Remover partículas
        for particle in particles_to_remove:
            self.particles.remove(particle)
    
    def run_scientific_simulation(self):
        """Ejecutar simulación científica en segundo plano"""
        try:
            self.simulation_results = self.pilot_sim.run_pilot_experiment(
                coagulant_dose=self.control_panel.coagulant_dose
            )
            
            # Los valores finales se usarán para calcular la progresión
            print("✓ Simulación científica completada")
            
        except Exception as e:
            print(f"Error en simulación científica: {e}")
    
    def update_progressive_simulation(self, dt):
        """Actualizar simulación progresivamente en el tiempo"""
        if not self.simulation_running or not self.simulation_results:
            return
        
        # Tiempo total de retención del sistema (calculado con volúmenes REALES)
        # Volúmenes reales: Caja 1: 12.2 L, Caja 2: 9.7 L, Caja 3: 9.7 L = 31.6 L total
        # Con caudal de 0.45 L/s: tiempo = 31.6 / 0.45 = 70.2 s
        total_volume_liters = 12.2 + 9.7 + 9.7  # L (volúmenes reales)
        total_retention_time = total_volume_liters / self.control_panel.flow_rate  # s
        
        # Incrementar progreso basado en el tiempo
        progress_increment = dt / total_retention_time
        self.simulation_progress += progress_increment
        
        # Si llega al 100%, reiniciar el ciclo para que fluya continuamente
        if self.simulation_progress >= 1.0:
            print("🔄 Ciclo completado - Continuando simulación...")
            # Mantener el progreso en estado estacionario (estado final permanente)
            self.simulation_progress = 1.0
        
        # Asegurar que los parámetros hidráulicos estén actualizados antes de calcular eficiencias
        self.update_tanks_hydraulics()
        
        # Usar valores configurables del panel de control
        initial_turbidity = self.control_panel.initial_turbidity
        initial_pH = self.control_panel.initial_pH
        
        # Obtener pH final de la simulación
        final_pH = self.simulation_results['after_coagulation']['pH']
        
        # === CÁLCULO AUTOMÁTICO DE EFICIENCIAS BASADO EN PARÁMETROS HIDRÁULICOS ===
        # Las eficiencias se calculan automáticamente desde los parámetros físicos del sistema
        
        # Mezcla rápida: eficiencia fija (principalmente coagulación, no remoción)
        eff_rapid_mix = 0.02      # 2% de remoción en mezcla rápida (principalmente coagulación)
        
        # Floculación: calcular desde parámetros hidráulicos
        floc_tank = self.tanks[1]  # Tanque de floculación
        if hasattr(floc_tank, 'hydraulic_params') and floc_tank.hydraulic_params:
            G_floc = floc_tank.hydraulic_params.get('gradient_G', 30)
            retention_time_floc = floc_tank.hydraulic_params.get('retention_time', 20)
            n_baffles = floc_tank.hydraulic_params.get('n_baffles', 7)
            coagulant_dose = self.control_panel.coagulant_dose
            
            # Calcular eficiencia automáticamente
            eff_flocculation = calculate_flocculation_efficiency(
                G_floc, retention_time_floc, n_baffles, coagulant_dose
            )
        else:
            # Valor por defecto si no hay parámetros calculados
            eff_flocculation = 0.37
        
        # Sedimentación: calcular desde parámetros hidráulicos
        sed_tank = self.tanks[2]  # Tanque de sedimentación
        if hasattr(sed_tank, 'hydraulic_params') and sed_tank.hydraulic_params:
            surface_loading = sed_tank.hydraulic_params.get('surface_loading', 40)
            retention_time_sed = sed_tank.hydraulic_params.get('retention_time', 20)
            height = sed_tank.real_height * 0.96  # Altura útil
            
            # Calcular eficiencia automáticamente
            eff_sedimentation = calculate_sedimentation_efficiency(
                surface_loading, retention_time_sed, height, 
                initial_turbidity, floc_density=1200
            )
        else:
            # Valor por defecto si no hay parámetros calculados
            eff_sedimentation = 0.68
        
        # Eficiencia total del sistema usando fórmula correcta para procesos en serie:
        # E_total = 100 × (1 - ∏(1 - Ei/100))
        # E_total = 100 × (1 - (1-E1)×(1-E2)×(1-E3))
        system_efficiency = 1 - ((1 - eff_rapid_mix) * (1 - eff_flocculation) * (1 - eff_sedimentation))
        final_turbidity = initial_turbidity * (1 - system_efficiency)  # Turbidez final = inicial × (1 - eficiencia)
        
        # Añadir fluctuaciones realistas (turbulencia, mezcla no perfecta)
        import random
        fluctuation = random.uniform(-0.02, 0.02)  # ±2% de fluctuación
        
        # === CAJA 1: MEZCLA RÁPIDA ===
        # En mezcla rápida: se añade coagulante, cambia pH rápidamente, ligera reducción de turbidez
        if self.simulation_progress < 0.4:  # Primeros 40% del tiempo
            progress_rm = min(1.0, self.simulation_progress / 0.4)
            
            # pH baja rápidamente por adición de coagulante (con fluctuación)
            base_pH = initial_pH - (initial_pH - final_pH) * progress_rm * 0.8
            self.water_state['rapid_mix']['pH'] = base_pH + fluctuation * 0.1
            
            # Turbidez: remoción del 2% (fórmula correcta: Cf = Ci × (1 - E))
            turbidity_after_rm = initial_turbidity * (1 - eff_rapid_mix * progress_rm)
            self.water_state['rapid_mix']['turbidity'] = turbidity_after_rm * (1 + fluctuation)
            self.water_state['rapid_mix']['color_turbidity'] = self.water_state['rapid_mix']['turbidity']
            
            # Eficiencia de mezcla rápida (% de remoción respecto a la entrada)
            self.tanks[0].efficiency = eff_rapid_mix * 100 * progress_rm  # 0-2%
            
        else:
            base_pH = initial_pH - (initial_pH - final_pH) * 0.8
            self.water_state['rapid_mix']['pH'] = base_pH + fluctuation * 0.1
            
            turbidity_after_rm = initial_turbidity * (1 - eff_rapid_mix)
            self.water_state['rapid_mix']['turbidity'] = turbidity_after_rm * (1 + fluctuation)
            self.water_state['rapid_mix']['color_turbidity'] = self.water_state['rapid_mix']['turbidity']
            self.tanks[0].efficiency = eff_rapid_mix * 100  # 2%
        
        # === CAJA 2: FLOCULACIÓN ===
        # En floculación: pH se estabiliza, turbidez baja ligeramente, formación de flóculos
        if self.simulation_progress >= 0.4 and self.simulation_progress < 0.8:
            progress_floc = (self.simulation_progress - 0.4) / 0.4
            
            # pH continúa bajando lentamente (con fluctuación menor)
            base_pH_floc = self.water_state['rapid_mix']['pH'] - (initial_pH - final_pH) * 0.2 * progress_floc
            self.water_state['flocculation']['pH'] = base_pH_floc + fluctuation * 0.05
            
            # Turbidez: remoción calculada automáticamente desde parámetros hidráulicos (fórmula correcta)
            turbidity_entering_floc = self.water_state['rapid_mix']['turbidity']
            turbidity_after_floc = turbidity_entering_floc * (1 - eff_flocculation * progress_floc)
            self.water_state['flocculation']['turbidity'] = turbidity_after_floc * (1 + fluctuation * 0.5)
            self.water_state['flocculation']['color_turbidity'] = self.water_state['flocculation']['turbidity']
            
            # Eficiencia de floculación (% de remoción respecto a lo que ENTRA)
            if turbidity_entering_floc > 0:
                actual_removal = (turbidity_entering_floc - self.water_state['flocculation']['turbidity']) / turbidity_entering_floc * 100
                self.tanks[1].efficiency = max(0, min(40, actual_removal))  # Límite ajustado a 37% objetivo
            else:
                self.tanks[1].efficiency = eff_flocculation * 100 * progress_floc
            
        elif self.simulation_progress >= 0.8:
            self.water_state['flocculation']['pH'] = final_pH + fluctuation * 0.03
            turbidity_entering_floc = self.water_state['rapid_mix']['turbidity']
            turbidity_after_floc = turbidity_entering_floc * (1 - eff_flocculation)
            self.water_state['flocculation']['turbidity'] = turbidity_after_floc * (1 + fluctuation * 0.3)
            self.water_state['flocculation']['color_turbidity'] = self.water_state['flocculation']['turbidity']
            
            if turbidity_entering_floc > 0:
                self.tanks[1].efficiency = (turbidity_entering_floc - self.water_state['flocculation']['turbidity']) / turbidity_entering_floc * 100
            else:
                self.tanks[1].efficiency = eff_flocculation * 100
        
        # === CAJA 3: SEDIMENTACIÓN ===
        # En sedimentación: pH estable, turbidez baja significativamente (la mayor reducción)
        if self.simulation_progress >= 0.8:
            progress_sed = (self.simulation_progress - 0.8) / 0.2
            
            # pH estable con fluctuación mínima
            self.water_state['sedimentation']['pH'] = final_pH + fluctuation * 0.02
            
            # Turbidez baja significativamente en el sedimentador
            # La sedimentación remueve 68% de la turbidez que entra (remoción importante pero no extrema)
            turbidity_after_floc = self.water_state['flocculation']['turbidity']
            
            # El sedimentador debe remover 68% de la turbidez que ENTRA (fórmula correcta)
            # Cf = Ci × (1 - E)
            # Interpolación progresiva desde turbidez después de floculación hasta turbidez final
            base_final_turbidity = turbidity_after_floc * (1 - eff_sedimentation * progress_sed)
            
            # Asegurar que la turbidez final sea coherente con la inicial
            self.water_state['sedimentation']['turbidity'] = max(0.1, base_final_turbidity * (1 + fluctuation * 0.1))
            self.water_state['sedimentation']['color_turbidity'] = self.water_state['sedimentation']['turbidity']
            
            # Calcular eficiencia del sedimentador específicamente (% de remoción respecto a lo que entra)
            # La eficiencia debe mostrar cuánto remueve el sedimentador de lo que ENTRA a él
            if turbidity_after_floc > 0:
                sed_removal_actual = (turbidity_after_floc - self.water_state['sedimentation']['turbidity']) / turbidity_after_floc * 100
                self.tanks[2].efficiency = min(75, max(0, sed_removal_actual))  # Límite 0-75% (ajustado a 68% objetivo)
            else:
                self.tanks[2].efficiency = eff_sedimentation * 100  # 68%
            
            # Imprimir información de depuración cada cierto tiempo
            if progress_sed >= 0.99:  # Cerca del final
                print(f"\n{'='*60}")
                print(f"📊 VERIFICACIÓN DE EFICIENCIAS DEL SISTEMA")
                print(f"{'='*60}")
                print(f"Turbidez INICIAL: {initial_turbidity:.2f} NTU")
                print(f"")
                print(f"CAJA 1 - Mezcla Rápida:")
                print(f"  Entrada: {initial_turbidity:.2f} NTU")
                print(f"  Salida: {self.water_state['rapid_mix']['turbidity']:.2f} NTU")
                print(f"  Eficiencia: {self.tanks[0].efficiency:.1f}%")
                print(f"")
                print(f"CAJA 2 - Floculación:")
                print(f"  Entrada: {self.water_state['rapid_mix']['turbidity']:.2f} NTU")
                print(f"  Salida: {turbidity_after_floc:.2f} NTU")
                print(f"  Eficiencia: {self.tanks[1].efficiency:.1f}%")
                print(f"")
                print(f"CAJA 3 - Sedimentación:")
                print(f"  Entrada: {turbidity_after_floc:.2f} NTU")
                print(f"  Salida: {self.water_state['sedimentation']['turbidity']:.2f} NTU")
                print(f"  Eficiencia: {self.tanks[2].efficiency:.1f}% ⭐ (MAYOR REMOCIÓN)")
                print(f"")
                print(f"EFICIENCIA TOTAL DEL SISTEMA:")
                print(f"  Fórmula: E_total = 100 × (1 - (1-E1)(1-E2)(1-E3))")
                print(f"  E_total = 100 × (1 - (1-{self.tanks[0].efficiency/100:.3f})(1-{self.tanks[1].efficiency/100:.3f})(1-{self.tanks[2].efficiency/100:.3f}))")
                print(f"  E_total = {system_efficiency*100:.1f}%")
                print(f"")
                print(f"Turbidez FINAL: {self.water_state['sedimentation']['turbidity']:.2f} NTU")
                print(f"{'='*60}\n")
        else:
            # Antes de llegar a sedimentación, mantener valores previos
            self.water_state['sedimentation']['pH'] = self.water_state['flocculation']['pH']
            self.water_state['sedimentation']['turbidity'] = self.water_state['flocculation']['turbidity']
            self.water_state['sedimentation']['color_turbidity'] = self.water_state['flocculation']['color_turbidity']
        
        # Actualizar colores de los tanques según turbidez
        self.update_tank_colors()
    
    def draw_pipes(self):
        """Dibujar tuberías conectoras reales (PVC 1/2") con MEDIDAS EXACTAS"""
        
        # Escala para convertir cm a píxeles (aproximadamente 1 cm = 3-4 píxeles)
        cm_to_px = 3.5
        
        # === CONEXIÓN CAJA 1 -> CAJA 2 (MEDIDAS REALES) ===
        # Salida de mezcla rápida
        pipe1_start_x = self.tanks[0].x + self.tanks[0].width
        pipe1_start_y = self.tanks[0].y + self.tanks[0].depth - 30  # Salida por ventana inferior
        
        # Tramo 1: Tubo largo de 19 cm (horizontal)
        pipe1_tramo1_x = pipe1_start_x + int(19 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe1_start_x, pipe1_start_y),
                        (pipe1_tramo1_x, pipe1_start_y), 8)
        
        # Codo 1: Baja 3 cm (vertical)
        pipe1_codo1_y = pipe1_start_y + int(3 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe1_tramo1_x, pipe1_start_y),
                        (pipe1_tramo1_x, pipe1_codo1_y), 8)
        pygame.draw.circle(screen, COLORS['pipe'], 
                          (pipe1_tramo1_x, pipe1_start_y), 6)
        
        # Tramo 2: Otro codo de largo 10 cm (horizontal)
        pipe1_tramo2_x = pipe1_tramo1_x + int(10 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe1_tramo1_x, pipe1_codo1_y),
                        (pipe1_tramo2_x, pipe1_codo1_y), 8)
        pygame.draw.circle(screen, COLORS['pipe'], 
                          (pipe1_tramo1_x, pipe1_codo1_y), 6)
        
        # Entrada a floculación (conectar al tanque)
        pipe1_end_x = self.tanks[1].x - 5
        pipe1_end_y = pipe1_codo1_y
        
        # Tramo final horizontal hasta entrada
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe1_tramo2_x, pipe1_codo1_y),
                        (pipe1_end_x, pipe1_end_y), 8)
        
        # === CONEXIÓN CAJA 2 -> CAJA 3 (MEDIDAS REALES) ===
        pipe2_start_x = self.tanks[1].x + self.tanks[1].width
        pipe2_start_y = self.tanks[1].y + self.tanks[1].depth - 30  # Salida por ventana inferior
        
        # Tramo 1: Codo de largo 3.5 cm (horizontal)
        pipe2_tramo1_x = pipe2_start_x + int(3.5 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe2_start_x, pipe2_start_y),
                        (pipe2_tramo1_x, pipe2_start_y), 8)
        
        # Codo 1: Baja 1.5 cm (vertical)
        pipe2_codo1_y = pipe2_start_y + int(1.5 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe2_tramo1_x, pipe2_start_y),
                        (pipe2_tramo1_x, pipe2_codo1_y), 8)
        pygame.draw.circle(screen, COLORS['pipe'], 
                          (pipe2_tramo1_x, pipe2_start_y), 6)
        
        # Tramo 2: Tubo de 9 cm de largo (horizontal)
        pipe2_tramo2_x = pipe2_tramo1_x + int(9 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe2_tramo1_x, pipe2_codo1_y),
                        (pipe2_tramo2_x, pipe2_codo1_y), 8)
        pygame.draw.circle(screen, COLORS['pipe'], 
                          (pipe2_tramo1_x, pipe2_codo1_y), 6)
        
        # Tramo 3: Conecta con 3.5 cm (horizontal)
        pipe2_tramo3_x = pipe2_tramo2_x + int(3.5 * cm_to_px)
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe2_tramo2_x, pipe2_codo1_y),
                        (pipe2_tramo3_x, pipe2_codo1_y), 8)
        
        # Entrada a sedimentador
        pipe2_end_x = self.tanks[2].x - 5
        pipe2_end_y = pipe2_codo1_y
        
        # Tramo final hasta entrada
        pygame.draw.line(screen, COLORS['pipe'],
                        (pipe2_tramo3_x, pipe2_codo1_y),
                        (pipe2_end_x, pipe2_end_y), 8)
        
        # === EMBUDO DE ENTRADA Y TUBERÍA PRINCIPAL ===
        # Embudo antes de la entrada (con forma de embudo invertido)
        funnel_start_x = 30
        funnel_top_y = self.tanks[0].y + self.tanks[0].depth // 2 - 25
        funnel_bottom_y = self.tanks[0].y + self.tanks[0].depth // 2
        funnel_top_width = 40
        funnel_bottom_width = 15
        
        # Dibujar embudo (trapecio invertido)
        funnel_points = [
            (funnel_start_x, funnel_top_y),  # Esquina superior izquierda
            (funnel_start_x + funnel_top_width, funnel_top_y),  # Esquina superior derecha
            (funnel_start_x + funnel_top_width - (funnel_top_width - funnel_bottom_width) // 2, funnel_bottom_y),  # Esquina inferior derecha
            (funnel_start_x + (funnel_top_width - funnel_bottom_width) // 2, funnel_bottom_y)  # Esquina inferior izquierda
        ]
        pygame.draw.polygon(screen, COLORS['pipe'], funnel_points)
        pygame.draw.polygon(screen, COLORS['tank_border'], funnel_points, 2)
        
        # Etiqueta del embudo
        funnel_label = font_small.render("EMBUDO", True, COLORS['text'])
        screen.blit(funnel_label, (funnel_start_x + 5, funnel_top_y - 20))
        
        # Tubería de entrada principal (desde el embudo hasta la mezcla rápida)
        inlet_start_x = funnel_start_x + funnel_top_width // 2
        inlet_start_y = funnel_bottom_y
        inlet_end_x = self.tanks[0].x - 20
        inlet_end_y = self.tanks[0].y + self.tanks[0].depth // 2
        
        # Tubería horizontal de entrada
        pygame.draw.line(screen, COLORS['pipe'], 
                        (inlet_start_x, inlet_start_y), 
                        (inlet_end_x, inlet_end_y), 8)
        
        # Indicador de dosificación de coagulante en la mezcla rápida
        # El coagulante se dosifica proporcionalmente: 10 unidades por cada 4 litros de agua
        # Esta información se muestra en el tanque de mezcla rápida
        
        # === TUBERÍA DE SALIDA DEL EFLUENTE ===
        # Tubería de salida del efluente (desde tubos de recolección)
        outlet_start_x = self.tanks[2].x + self.tanks[2].width // 2
        outlet_start_y = self.tanks[2].y + 5
        outlet_end_x = outlet_start_x + 100
        outlet_end_y = outlet_start_y
        
        pygame.draw.line(screen, COLORS['pipe'],
                        (outlet_start_x, outlet_start_y),
                        (outlet_end_x, outlet_end_y), 8)
        
        # === ETIQUETAS DE TUBERÍAS ===
        font_pipe = pygame.font.Font(None, 16)
        
        # Entrada
        inlet_label = font_pipe.render("Entrada Q=0.45 L/s", True, COLORS['text'])
        screen.blit(inlet_label, (inlet_start_x, inlet_start_y - 20))
        
        # Conexiones
        conn1_label = font_pipe.render("PVC 1/2\"", True, COLORS['text'])
        screen.blit(conn1_label, (pipe1_start_x + 35, pipe1_start_y - 15))
        
        conn2_label = font_pipe.render("PVC 1/2\"", True, COLORS['text'])
        screen.blit(conn2_label, (pipe2_start_x + 45, pipe2_start_y - 15))
        
        # Salida
        outlet_label = font_pipe.render("Efluente", True, COLORS['text'])
        screen.blit(outlet_label, (outlet_end_x - 30, outlet_end_y - 20))
    
    def draw_flow_arrows(self):
        """Dibujar flechas de flujo animadas en disposición vertical"""
        # Velocidad de animación de flechas depende de la velocidad de simulación
        arrow_speed = 50 * self.control_panel.simulation_speed
        arrow_offset = int(time.time() * arrow_speed) % 30
        
        # Flecha en tubería de entrada
        inlet_y = self.tanks[0].y + self.tanks[0].depth // 2
        inlet_positions = [
            (100 + arrow_offset, inlet_y),
            (130 + arrow_offset, inlet_y)
        ]
        
        for x, y in inlet_positions:
            if 50 <= x <= 180:
                pygame.draw.polygon(screen, COLORS['water_clean'], [
                    (x, y - 3), (x + 10, y), (x, y + 3), (x + 3, y)
                ])
        
        # Flechas en conexiones verticales
        # Conexión 1->2
        pipe1_x = self.tanks[0].x + self.tanks[0].width + 55
        pipe1_y_start = self.tanks[0].y + self.tanks[0].depth - 40
        pipe1_y_end = self.tanks[1].y + self.tanks[1].depth - 40
        
        # Flechas verticales descendentes
        for i in range(3):
            arrow_y = pipe1_y_start + arrow_offset + i * 40
            if pipe1_y_start <= arrow_y <= pipe1_y_end - 10:
                pygame.draw.polygon(screen, COLORS['water_clean'], [
                    (pipe1_x - 3, arrow_y), (pipe1_x, arrow_y + 10), 
                    (pipe1_x + 3, arrow_y), (pipe1_x, arrow_y + 3)
                ])
        
        # Conexión 2->3
        pipe2_x = self.tanks[1].x + self.tanks[1].width + 65
        pipe2_y_start = self.tanks[1].y + self.tanks[1].depth - 40
        pipe2_y_end = self.tanks[2].y + self.tanks[2].depth - 40
        
        for i in range(3):
            arrow_y = pipe2_y_start + arrow_offset + i * 40
            if pipe2_y_start <= arrow_y <= pipe2_y_end - 10:
                pygame.draw.polygon(screen, COLORS['water_clean'], [
                    (pipe2_x - 3, arrow_y), (pipe2_x, arrow_y + 10), 
                    (pipe2_x + 3, arrow_y), (pipe2_x, arrow_y + 3)
                ])
        
        # Flecha en salida del efluente
        outlet_x = self.tanks[2].x + self.tanks[2].width // 2
        outlet_y = self.tanks[2].y + 5
        
        outlet_positions = [
            (outlet_x + 20 + arrow_offset, outlet_y),
            (outlet_x + 50 + arrow_offset, outlet_y)
        ]
        
        for x, y in outlet_positions:
            if outlet_x <= x <= outlet_x + 90:
                pygame.draw.polygon(screen, COLORS['water_clean'], [
                    (x, y - 3), (x + 10, y), (x, y + 3), (x + 3, y)
                ])
    
    def draw_results_panel(self):
        """Dibujar panel de resultados con ajuste automático"""
        # Fondo del panel con gradiente más oscuro para mejor contraste
        pygame.draw.rect(screen, (20, 28, 40), RESULTS_PANEL)
        pygame.draw.rect(screen, COLORS['tank_border'], RESULTS_PANEL, 3)
        
        # Calcular dimensiones adaptativas basadas en el tamaño del panel
        panel_width = RESULTS_PANEL.width
        panel_height = RESULTS_PANEL.height
        
        # Título del panel - tamaño adaptativo
        title_size = max(18, int(panel_height * 0.08))
        title_font = pygame.font.Font(None, title_size)
        title = title_font.render("RESULTADOS DE LA SIMULACIÓN", True, (100, 255, 150))
        title_rect = title.get_rect(centerx=RESULTS_PANEL.centerx, y=RESULTS_PANEL.y + int(panel_height * 0.03))
        screen.blit(title, title_rect)
        
        # Línea separadora debajo del título - posición adaptativa
        title_bottom = RESULTS_PANEL.y + int(panel_height * 0.12)
        pygame.draw.line(screen, (100, 255, 150), 
                        (RESULTS_PANEL.x + 20, title_bottom),
                        (RESULTS_PANEL.x + RESULTS_PANEL.width - 20, title_bottom), 2)
        
        if self.simulation_results and self.simulation_progress > 0.1:
            # Calcular espacio disponible para contenido
            content_top = title_bottom + 10
            compliance_height = max(25, int(panel_height * 0.12))  # Altura de indicadores
            content_height = panel_height - (content_top - RESULTS_PANEL.y) - compliance_height - 10
            
            # Organizar resultados en columnas con espaciado adaptativo
            margin_x = max(15, int(panel_width * 0.02))
            col_width = (panel_width - 4 * margin_x) // 3
            col1_x = RESULTS_PANEL.x + margin_x
            col2_x = col1_x + col_width + margin_x
            col3_x = col2_x + col_width + margin_x
            results_y = content_top
            
            # Calcular espaciado vertical adaptativo
            line_spacing = max(14, int(content_height * 0.04))  # Espaciado entre líneas
            small_font_size = max(12, int(panel_height * 0.05))
            medium_font_size = max(16, int(panel_height * 0.06))
            large_font_size = max(24, int(panel_height * 0.10))
            
            font_small_adaptive = pygame.font.Font(None, small_font_size)
            font_medium_adaptive = pygame.font.Font(None, medium_font_size)
            font_large_adaptive = pygame.font.Font(None, large_font_size)
            
            # === COLUMNA 1: EFICIENCIAS ===
            # Calcular eficiencia total del sistema correctamente
            turb_initial = self.control_panel.initial_turbidity
            turb_final = self.water_state['sedimentation']['turbidity']
            
            # Eficiencia total corregida (nunca puede ser > 100%)
            if turb_initial > 0:
                total_removal = max(0, min(100, ((turb_initial - turb_final) / turb_initial * 100)))
            else:
                total_removal = 0
            
            # Usar la eficiencia calculada correctamente
            efficiency = total_removal
            efficiency = min(100, max(0, efficiency))
            
            # Fondo de sección - altura adaptativa
            section_height = content_height
            section_rect1 = pygame.Rect(col1_x - 10, results_y - 5, col_width, section_height)
            pygame.draw.rect(screen, (30, 40, 55), section_rect1)
            pygame.draw.rect(screen, (100, 255, 100), section_rect1, 2)
            
            # Título de sección
            current_y = results_y
            eff_title = font_medium_adaptive.render("EFICIENCIAS", True, (100, 255, 100))
            screen.blit(eff_title, (col1_x, current_y))
            current_y += line_spacing + 5
            
            # Mostrar eficiencia con fuente grande y colores graduales
            eff_text = f"{efficiency:.1f}%"
            if efficiency >= 95:
                eff_color = COLORS['success']
            elif efficiency >= 85:
                eff_color = (100, 255, 150)
            elif efficiency >= 70:
                eff_color = COLORS['warning']
            else:
                eff_color = COLORS['error']
            eff_surface = font_large_adaptive.render(eff_text, True, eff_color)
            screen.blit(eff_surface, (col1_x, current_y))
            current_y += large_font_size + 5
            
            # Etiqueta "Eficiencia Total"
            eff_label = font_small_adaptive.render("Eficiencia Total", True, (180, 180, 180))
            screen.blit(eff_label, (col1_x, current_y))
            current_y += line_spacing + 3
            
            # Barra de progreso adaptativa
            bar_width = col_width - 20
            bar_height = max(12, int(content_height * 0.08))
            bar_x = col1_x
            bar_y = current_y
            
            # Fondo de la barra
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
            # Barra de llenado
            fill_width = max(2, int(bar_width * efficiency / 100))
            pygame.draw.rect(screen, eff_color, (bar_x, bar_y, fill_width, bar_height))
            # Borde
            pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)
            current_y += bar_height + line_spacing
            
            # Eficiencias por etapa - espaciado adaptativo
            eff_label_small = font_small_adaptive.render("Por Etapa:", True, (150, 200, 255))
            screen.blit(eff_label_small, (col1_x, current_y))
            current_y += line_spacing
            
            eff_stages = [
                f"Mezcla Rapida: {self.tanks[0].efficiency:.1f}%",
                f"Floculacion: {self.tanks[1].efficiency:.1f}%",
                f"Sedimentacion: {self.tanks[2].efficiency:.1f}%"
            ]
            for i, stage_text in enumerate(eff_stages):
                stage_surface = font_small_adaptive.render(stage_text, True, (200, 200, 200))
                screen.blit(stage_surface, (col1_x, current_y))
                current_y += line_spacing
            
            # === COLUMNA 2: CALIDAD DEL AGUA ===
            # Fondo de sección - altura adaptativa
            section_rect2 = pygame.Rect(col2_x - 10, results_y - 5, col_width, content_height)
            pygame.draw.rect(screen, (30, 40, 55), section_rect2)
            pygame.draw.rect(screen, (100, 200, 255), section_rect2, 2)
            
            # Título de sección
            current_y = results_y
            quality_title = font_medium_adaptive.render("CALIDAD DEL AGUA", True, (100, 200, 255))
            screen.blit(quality_title, (col2_x, current_y))
            current_y += line_spacing + 5
            
            # Valores de turbidez y pH
            turb_rm = self.water_state['rapid_mix']['turbidity']
            turb_floc = self.water_state['flocculation']['turbidity']
            turb_sed = self.water_state['sedimentation']['turbidity']
            ph_final = self.simulation_results['after_coagulation']['pH']
            
            # pH destacado
            ph_label = font_small_adaptive.render("pH Final:", True, (180, 180, 180))
            screen.blit(ph_label, (col2_x, current_y))
            ph_value = font_medium_adaptive.render(f"{ph_final:.2f}", True, (100, 255, 200))
            screen.blit(ph_value, (col2_x + 80, current_y))
            current_y += line_spacing + 3
            
            # Turbidez - Progresión clara
            turb_label = font_small_adaptive.render("Turbidez (NTU):", True, (180, 180, 180))
            screen.blit(turb_label, (col2_x, current_y))
            current_y += line_spacing
            
            # Mostrar progresión de turbidez con flechas
            turb_values = [
                ("Entrada", self.control_panel.initial_turbidity, (255, 200, 100)),
                ("→ Mezcla Rapida", turb_rm, (150, 220, 255)),
                ("→ Floculacion", turb_floc, (150, 220, 255)),
                ("→ Sedimentacion", turb_sed, (100, 255, 150))
            ]
            
            for i, (stage, value, color) in enumerate(turb_values):
                # Calcular reducción porcentual respecto a la entrada
                if i > 0 and self.control_panel.initial_turbidity > 0:
                    reduction = ((self.control_panel.initial_turbidity - value) / self.control_panel.initial_turbidity * 100)
                    stage_text = f"{stage}: {value:.1f} NTU ({reduction:.0f}%)"
                else:
                    stage_text = f"{stage}: {value:.1f} NTU"
                stage_surface = font_small_adaptive.render(stage_text, True, color)
                screen.blit(stage_surface, (col2_x, current_y))
                current_y += line_spacing
            
            # Remoción total - posición calculada dinámicamente
            current_y += 3  # Espacio adicional antes de remoción
            if turb_initial > 0:
                removal_pct = max(0, min(100, ((turb_initial - turb_sed) / turb_initial * 100)))
            else:
                removal_pct = 0
            
            # Remoción total con mejor formato y colores
            removal_text = f"Remocion Total: {removal_pct:.1f}%"
            if removal_pct >= 95:
                removal_color = COLORS['success']
            elif removal_pct >= 85:
                removal_color = (100, 255, 150)
            elif removal_pct >= 70:
                removal_color = COLORS['warning']
            else:
                removal_color = COLORS['error']
            removal_surface = font_medium_adaptive.render(removal_text, True, removal_color)
            screen.blit(removal_surface, (col2_x, current_y))
            
            # === COLUMNA 3: PARÁMETROS PROCESO ===
            # Fondo de sección - altura adaptativa
            section_rect3 = pygame.Rect(col3_x - 10, results_y - 5, col_width, content_height)
            pygame.draw.rect(screen, (30, 40, 55), section_rect3)
            pygame.draw.rect(screen, (255, 200, 100), section_rect3, 2)
            
            # Título de sección
            current_y = results_y
            process_title = font_medium_adaptive.render("PARAMETROS PROCESO", True, (255, 200, 100))
            screen.blit(process_title, (col3_x, current_y))
            current_y += line_spacing + 5
            
            # Calcular dosis de coagulante real
            coagulant_dose_real = self.calculate_coagulant_dose()
            
            # Parámetros con formato adaptativo
            params = [
                ("Dosis Coagulante", f"{coagulant_dose_real:.1f} (10/4L)", (255, 220, 150)),
                ("Caudal", f"{self.control_panel.flow_rate:.2f} L/s", (200, 200, 200)),
                ("Tiempo Simulado", f"{self.simulation_time:.1f} s", (200, 200, 200)),
                ("Progreso", f"{self.simulation_progress*100:.1f}%", (150, 200, 255))
            ]
            
            for i, (label, value, color) in enumerate(params):
                label_surface = font_small_adaptive.render(f"{label}:", True, (180, 180, 180))
                screen.blit(label_surface, (col3_x, current_y))
                value_surface = font_small_adaptive.render(value, True, color)
                screen.blit(value_surface, (col3_x + 120, current_y))
                current_y += line_spacing
            
            # === INDICADORES DE CUMPLIMIENTO (fila inferior) ===
            # Posición adaptativa - calcular desde el fondo del panel
            compliance_height = max(25, int(panel_height * 0.12))
            compliance_y = RESULTS_PANEL.y + RESULTS_PANEL.height - compliance_height - 5
            
            # Fondo para indicadores
            compliance_rect = pygame.Rect(RESULTS_PANEL.x + 10, compliance_y - 3, 
                                         RESULTS_PANEL.width - 20, compliance_height)
            pygame.draw.rect(screen, (25, 35, 50), compliance_rect)
            pygame.draw.rect(screen, (100, 150, 200), compliance_rect, 2)
            
            # pH en rango
            ph_ok = 6.5 <= ph_final <= 8.5
            ph_indicator = "pH: OK" if ph_ok else "pH: FUERA DE RANGO"
            ph_color_ind = COLORS['success'] if ph_ok else COLORS['error']
            ph_surface = font_small_adaptive.render(ph_indicator, True, ph_color_ind)
            screen.blit(ph_surface, (col1_x, compliance_y))
            
            # Turbidez con rangos más realistas
            if turb_sed <= 1.0:
                turb_status = "EXCELENTE"
                turb_color_ind = COLORS['success']
            elif turb_sed <= 5.0:
                turb_status = "OK"
                turb_color_ind = COLORS['success']
            elif turb_sed <= 10.0:
                turb_status = "ACEPTABLE"
                turb_color_ind = COLORS['warning']
            else:
                turb_status = "ALTA"
                turb_color_ind = COLORS['error']
            turb_indicator = f"Turbidez: {turb_status} ({turb_sed:.1f} NTU)"
            turb_surface = font_small_adaptive.render(turb_indicator, True, turb_color_ind)
            screen.blit(turb_surface, (col2_x, compliance_y))
            
            # Eficiencia con rangos más realistas
            if efficiency >= 95:
                eff_status = "EXCELENTE"
                eff_ind_color = COLORS['success']
            elif efficiency >= 85:
                eff_status = "BUENA"
                eff_ind_color = (100, 255, 150)
            elif efficiency >= 70:
                eff_status = "ACEPTABLE"
                eff_ind_color = COLORS['warning']
            else:
                eff_status = "BAJA"
                eff_ind_color = COLORS['error']
            eff_indicator = f"Eficiencia: {eff_status} ({efficiency:.1f}%)"
            eff_ind_surface = font_small_adaptive.render(eff_indicator, True, eff_ind_color)
            screen.blit(eff_ind_surface, (col3_x, compliance_y))
            
        else:
            # Mensaje cuando no hay resultados - mejorado
            msg_rect = pygame.Rect(RESULTS_PANEL.x + 20, RESULTS_PANEL.y + 60, 
                                  RESULTS_PANEL.width - 40, RESULTS_PANEL.height - 80)
            pygame.draw.rect(screen, (30, 40, 55), msg_rect)
            pygame.draw.rect(screen, (100, 150, 200), msg_rect, 2)
            
            if not self.simulation_running:
                no_results = font_large.render("Presiona INICIAR para ejecutar", True, (200, 200, 200))
                no_results2 = font_medium.render("la simulacion", True, (150, 150, 150))
            else:
                no_results = font_large.render("Simulacion en progreso...", True, (255, 200, 100))
                no_results2 = font_medium.render("Espera unos segundos", True, (200, 200, 200))
            
            no_results_rect = no_results.get_rect(center=(msg_rect.centerx, msg_rect.centery - 15))
            no_results2_rect = no_results2.get_rect(center=(msg_rect.centerx, msg_rect.centery + 15))
            screen.blit(no_results, no_results_rect)
            screen.blit(no_results2, no_results2_rect)
    
    def handle_events(self):
        """Manejar eventos de Pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Eventos del panel de control
            action = self.control_panel.handle_event(event)
            
            if action == 'toggle_simulation':
                self.simulation_running = not self.simulation_running
                self.control_panel.running = self.simulation_running
                
                if self.simulation_running:
                    print("🚀 Iniciando simulación científica...")
                    # Iniciar logging de datos
                    if hasattr(self, 'data_logger'):
                        self.data_logger.start_logging()
                    # Ejecutar simulación científica en hilo separado
                    threading.Thread(target=self.run_scientific_simulation, daemon=True).start()
                else:
                    print("⏸️ Simulación detenida")
            
            elif action == 'pause_simulation':
                self.simulation_running = False
                self.control_panel.running = False
                # Detener logging de datos
                if hasattr(self, 'data_logger'):
                    self.data_logger.stop_logging()
                print("⏸️ Simulación pausada")
            
            elif action == 'reset_simulation':
                self.simulation_running = False
                self.control_panel.running = False
                self.particles.clear()
                self.simulation_time = 0
                self.simulation_results = None
                self.simulation_progress = 0.0
                
                # Resetear y detener logging de datos
                if hasattr(self, 'data_logger'):
                    self.data_logger.stop_logging()
                    self.data_logger = PlantDataLogger()  # Crear nuevo logger
                
                # Resetear estado del agua usando valores configurables
                initial_turbidity = self.control_panel.initial_turbidity
                initial_pH = self.control_panel.initial_pH
                
                initial_state = {
                    'turbidity': initial_turbidity,
                    'pH': initial_pH,
                    'color_turbidity': initial_turbidity,
                    'particles_removed': 0.0
                }
                self.water_state = {
                    'rapid_mix': initial_state.copy(),
                    'flocculation': initial_state.copy(),
                    'sedimentation': initial_state.copy()
                }
                
                for tank in self.tanks:
                    tank.efficiency = 0
                    tank.current_turbidity = initial_turbidity
                
                print("🔄 Simulación reiniciada")
                print(f"   pH inicial: {initial_pH:.2f}")
                print(f"   Turbidez inicial: {initial_turbidity:.1f} NTU")
                print(f"   Temperatura: {self.control_panel.water_temperature:.1f} °C")
            
            elif action == 'toggle_config':
                self.control_panel.show_config = not self.control_panel.show_config
                if self.control_panel.show_config:
                    print("⚙ Panel de configuraciones abierto")
                else:
                    print("⚙ Panel de configuraciones cerrado")
            
            elif action == 'toggle_advanced':
                self.control_panel.show_advanced_params = not self.control_panel.show_advanced_params
                if self.control_panel.show_advanced_params:
                    print("📊 Panel de parámetros avanzados abierto")
                else:
                    print("📊 Panel de parámetros avanzados cerrado")
            
            elif action == 'exit_program':
                print("👋 Cerrando simulador...")
                self.running = False
            
            elif action == 'generate_graphs':
                print("📊 Generando gráficas de la planta piloto...")
                self.generate_plant_graphs()
            
            # Actualizar parámetros hidráulicos cuando cambia el caudal
            if hasattr(event, 'type') and event.type == pygame.MOUSEBUTTONDOWN:
                # Verificar si se movió el slider de caudal
                mouse_pos = pygame.mouse.get_pos()
                for slider_name, slider in self.control_panel.sliders.items():
                    if slider_name == 'flow_rate' and slider['rect'].collidepoint(mouse_pos):
                        # Actualizar tanques con nuevo caudal
                        self.update_tanks_hydraulics()
                        # Actualizar panel de control
                        self.control_panel.update_hydraulic_data()
                        break
            
            # Ya no necesitamos botones de velocidad, se maneja con el slider
    
    def run(self):
        """Bucle principal del juego"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time en segundos
            
            # Manejar eventos
            self.handle_events()
            
            # Actualizar simulación con velocidad ajustable
            if self.simulation_running:
                # Aplicar multiplicador de velocidad
                accelerated_dt = dt * self.control_panel.simulation_speed
                self.simulation_time += accelerated_dt
                
                # Actualizar simulación progresiva (cambios en turbidez, pH, etc.)
                self.update_progressive_simulation(accelerated_dt)
                
                # Registrar datos para gráficas
                if hasattr(self, 'data_logger') and self.simulation_results:
                    # Preparar datos de simulación
                    simulation_data = {
                        'overall_efficiency': self.simulation_results.get('final_efficiency', 75.0),
                        'sedimentation_efficiency': self.simulation_results.get('sedimentation_efficiency', 70.0),
                        'turbidity_out': self.water_state['sedimentation']['turbidity'],
                        'flocculation_G': self.tanks[1].hydraulic_params.get('gradient_G', 45.0) if hasattr(self.tanks[1], 'hydraulic_params') else 45.0
                    }
                    
                    # Preparar datos del panel de control
                    control_data = {
                        'flow_rate': self.control_panel.flow_rate,
                        'coagulant_dose': self.control_panel.coagulant_dose,
                        'pH': self.water_state['sedimentation']['pH'],
                        'temperature': self.control_panel.water_temperature,
                        'current_turbidity': self.water_state['sedimentation']['turbidity'],
                        'flocculation_G': simulation_data['flocculation_G']
                    }
                    
                    # Registrar datos
                    self.data_logger.log_simulation_data(simulation_data, control_data)
                
                # Generar partículas (la función ahora maneja la velocidad internamente)
                self.spawn_particles()
                
                # Actualizar partículas con tiempo acelerado
                self.update_particles(accelerated_dt)
            
            # Dibujar todo con layout organizado
            screen.fill(COLORS['background'])
            
            # Dibujar áreas de layout
            self.draw_layout_areas(screen)
            
            # Etiqueta de controles de velocidad en el área principal (siempre visible)
            speed_color = (255, 200, 100)
            if self.control_panel.simulation_speed >= 10:
                speed_color = (255, 100, 100)  # Rojo para velocidades altas
            elif self.control_panel.simulation_speed >= 5:
                speed_color = (255, 165, 0)  # Naranja para velocidad media-alta
            
            if self.simulation_running:
                speed_info = f"⚡ Velocidad: {self.control_panel.simulation_speed:.1f}x"
                if self.control_panel.simulation_speed >= 50:
                    speed_info = "🚀 Velocidad: MÁXIMA"
            else:
                speed_info = f"Velocidad: {self.control_panel.simulation_speed:.1f}x (Pausado)"
            
            speed_surface = font_medium.render(speed_info, True, speed_color)
            screen.blit(speed_surface, (MAIN_AREA.x + int(10 * font_scale), 
                                       MAIN_AREA.y + int(MAIN_AREA.height * 0.35)))
            
            # Título principal en header (adaptativo)
            title_text = "PLANTA PILOTO - SIMULADOR" if SCREEN_WIDTH < 1200 else "PLANTA PILOTO DE TRATAMIENTO DE AGUA - SIMULADOR"
            title = font_large.render(title_text, True, COLORS['text'])
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, HEADER_AREA.centery))
            screen.blit(title, title_rect)
            
            # Área principal - tanques y proceso
            pygame.draw.rect(screen, (30, 40, 55), MAIN_AREA)
            pygame.draw.rect(screen, COLORS['tank_border'], MAIN_AREA, 2)
            
            # Dibujar tuberías conectoras
            self.draw_pipes()
            
            # Actualizar pH en tanques antes de dibujar
            if self.simulation_running and self.simulation_results:
                self.tanks[0].current_pH = self.water_state['rapid_mix']['pH']
                self.tanks[1].current_pH = self.water_state['flocculation']['pH']
                self.tanks[2].current_pH = self.water_state['sedimentation']['pH']
            
            # Dibujar tanques
            for tank in self.tanks:
                tank.draw(screen)
            
            # Dibujar partículas
            for particle in self.particles:
                particle.draw(screen)
            
            # Dibujar flechas de flujo
            if self.simulation_running:
                self.draw_flow_arrows()
            
            # Panel de control
            self.control_panel.draw(screen)
            
            # Panel de resultados
            self.draw_results_panel()
            
            # Información de estado en el área principal
            if self.simulation_running and self.simulation_progress >= 1.0:
                status_text = "● ESTADO ESTACIONARIO (Equilibrio alcanzado)"
                status_color = (100, 255, 100)  # Verde brillante
            elif self.simulation_running:
                status_text = "● SIMULACIÓN ACTIVA"
                status_color = COLORS['success']
            else:
                status_text = "● SIMULACIÓN PAUSADA"
                status_color = COLORS['warning']
            
            status_surface = font_medium.render(status_text, True, status_color)
            screen.blit(status_surface, (MAIN_AREA.x + int(10 * font_scale), 
                                        MAIN_AREA.y + int(10 * font_scale)))
            
            # Información adicional
            speed_text = f"{self.control_panel.simulation_speed:.1f}x" if self.control_panel.simulation_speed < 50 else "MAX"
            
            # Calcular tiempo real vs tiempo simulado
            tiempo_real = self.simulation_time / max(1, self.control_panel.simulation_speed)
            
            info_texts = [
                f"Partículas activas: {len(self.particles)}",
                f"Tiempo simulado: {self.simulation_time:.1f}s",
                f"Progreso: {self.simulation_progress*100:.1f}%",
                f"Velocidad: {speed_text}",
                f"Dosis coagulante: {self.control_panel.coagulant_dose:.3f} g/L",
                f"Caudal: {self.control_panel.flow_rate:.2f} L/s"
            ]
            
            for i, text in enumerate(info_texts):
                info_surface = font_small.render(text, True, COLORS['text'])
                screen.blit(info_surface, (MAIN_AREA.x + int(10 * font_scale), 
                                          MAIN_AREA.y + int(35 * font_scale) + i * int(18 * font_scale)))
            
            # Actualizar pantalla
            pygame.display.flip()
        
        pygame.quit()
    
    def generate_plant_graphs(self):
        """Generar y mostrar gráficas de monitoreo de la planta piloto"""
        try:
            # Verificar si hay datos suficientes
            if not hasattr(self, 'data_logger') or len(self.data_logger.data_history['timestamps']) < 3:
                print("⚠️ No hay suficientes datos para generar gráficas")
                print("   Ejecuta la simulación por al menos 10 segundos para obtener datos")
                return
            
            # Mostrar ventana de gráficas
            self.graph_generator.show_graphs_window(self.data_logger)
            
        except Exception as e:
            print(f"❌ Error al generar gráficas: {e}")
            print("   Asegúrate de que la simulación haya estado ejecutándose")
    
    def draw_layout_areas(self, screen):
        """Dibujar las áreas del layout para mejor organización"""
        # Header area
        pygame.draw.rect(screen, (20, 30, 45), HEADER_AREA)
        pygame.draw.rect(screen, COLORS['tank_border'], HEADER_AREA, 2)

def main():
    """Función principal"""
    print("Iniciando simulador interactivo de planta piloto...")
    print("Controles:")
    print("- Boton INICIAR/PAUSAR: Controla la simulacion")
    print("- Slider Dosis: Ajusta la dosis de coagulante")
    print("- Slider Caudal: Ajusta el caudal de operacion")
    print("- Boton CONFIGURACIONES: Ajusta parametros del agua")
    print("- Boton RESET: Reinicia la simulacion")
    
    try:
        game = WaterTreatmentGame()
        game.run()
    except Exception as e:
        print(f"Error ejecutando el simulador: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()