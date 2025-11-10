# Sistema de Gráficas - Planta Piloto de Tratamiento de Agua

## 📊 Descripción

El sistema de gráficas permite visualizar en tiempo real los parámetros importantes de la planta piloto de tratamiento de agua, incluyendo:

1. **Velocidad de Sedimentación** (mm/s)
2. **Eficiencia del Sistema** (%)
3. **Turbidez del Efluente** (NTU)
4. **Color del Efluente** (Pt-Co)
5. **pH del Sistema**
6. **Parámetros Operativos** (Caudal y Dosis de Coagulante)

## 🚀 Cómo Usar

### Paso 1: Iniciar la Simulación
1. Ejecuta `python game_visualization.py` o `python test_graphs.py`
2. Presiona el botón **"INICIAR"** para comenzar la simulación
3. Espera al menos **10-15 segundos** para que se generen datos suficientes

### Paso 2: Generar Gráficas
1. Presiona el botón **"GENERAR GRAFICAS"** en el panel de control
2. Se abrirá una nueva ventana con 6 gráficas de monitoreo

### Paso 3: Interactuar con las Gráficas
En la ventana de gráficas puedes:
- **ESC**: Cerrar la ventana de gráficas
- **S**: Guardar las gráficas como archivo PNG
- **R**: Actualizar las gráficas con los datos más recientes

## 📈 Gráficas Disponibles

### 1. Velocidad de Sedimentación
- **Unidad**: mm/s
- **Descripción**: Velocidad a la que sedimentan las partículas floculadas
- **Cálculo**: Basado en la ecuación de Stokes modificada
- **Factores**: Tamaño de flóculo, gradiente G, tiempo de floculación

### 2. Eficiencia del Sistema
- **Unidad**: %
- **Líneas**: Eficiencia global y eficiencia de sedimentación
- **Descripción**: Porcentaje de remoción de contaminantes
- **Rango típico**: 70-95%

### 3. Turbidez del Efluente
- **Unidad**: NTU (Unidades Nefelométricas de Turbidez)
- **Límites**:
  - Verde (≤1.0 NTU): Excelente
  - Naranja (≤5.0 NTU): Bueno
  - Rojo (>5.0 NTU): Requiere ajuste

### 4. Color del Efluente
- **Unidad**: Pt-Co (Platino-Cobalto)
- **Límites**:
  - Verde (≤5.0 Pt-Co): Excelente
  - Naranja (≤15.0 Pt-Co): Aceptable
  - Rojo (>15.0 Pt-Co): Requiere ajuste

### 5. pH del Sistema
- **Unidad**: pH
- **Rango óptimo**: 6.5 - 8.5
- **Líneas de referencia**:
  - Verde (7.0): pH óptimo
  - Rojo (6.5 y 8.5): Límites aceptables

### 6. Parámetros Operativos
- **Caudal** (L/s): Flujo de agua a través del sistema
- **Dosis de Coagulante** (mg/L): Cantidad de coagulante añadido

## 🔧 Configuración

### Intervalo de Registro
- Los datos se registran cada **2 segundos** por defecto
- Se almacenan hasta **200 puntos** de datos (aproximadamente 6-7 minutos)

### Personalización
Puedes modificar los parámetros en `plant_graphs.py`:
```python
self.log_interval = 2.0  # Segundos entre registros
self.max_points = 200    # Máximo número de puntos
```

## 📁 Archivos del Sistema

- `plant_graphs.py`: Clases principales del sistema de gráficas
- `game_visualization.py`: Integración con el simulador principal
- `test_graphs.py`: Script de prueba
- `README_GRAFICAS.md`: Esta documentación

## 🐛 Solución de Problemas

### "No hay suficientes datos para generar gráficas"
- **Causa**: La simulación no ha estado ejecutándose el tiempo suficiente
- **Solución**: Ejecuta la simulación por al menos 10-15 segundos antes de generar gráficas

### Error al mostrar gráficas
- **Causa**: Problema con matplotlib o pygame
- **Solución**: Verifica que tengas instaladas las dependencias:
  ```bash
  pip install matplotlib pygame numpy
  ```

### Las gráficas no se actualizan
- **Causa**: La simulación está pausada o no hay nuevos datos
- **Solución**: Asegúrate de que la simulación esté ejecutándose activamente

## 📊 Interpretación de Resultados

### Valores Típicos Esperados
- **Velocidad de sedimentación**: 0.1 - 2.0 mm/s
- **Eficiencia global**: 75 - 90%
- **Turbidez final**: 1 - 5 NTU
- **Color final**: 5 - 15 Pt-Co
- **pH**: 6.8 - 7.5

### Indicadores de Buen Funcionamiento
- Eficiencia > 80%
- Turbidez < 5 NTU
- Color < 15 Pt-Co
- pH entre 6.5 - 8.5
- Velocidad de sedimentación estable

## 🔬 Base Científica

Las gráficas se basan en:
- **Ecuación de Stokes**: Para velocidad de sedimentación
- **Criterio de Camp**: Para eficiencia de floculación (G×t)
- **Teoría de Hazen**: Para sedimentación
- **Normas de calidad del agua**: Para límites de turbidez y color

## 📞 Soporte

Si encuentras problemas o tienes sugerencias, revisa:
1. Los mensajes de consola para errores específicos
2. Que todas las dependencias estén instaladas
3. Que la simulación esté ejecutándose correctamente

¡Disfruta monitoreando tu planta piloto! 🧪💧