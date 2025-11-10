# 📚 Ejemplos de Uso del Simulador

## 🎯 Casos de Uso Típicos

### 1. 🧪 Experimento Básico de Coagulación

**Objetivo**: Determinar la dosis óptima de coagulante

**Pasos**:
1. Configurar agua cruda con turbidez alta (80-100 NTU)
2. Variar dosis de coagulante (0.02 - 0.08 g/L)
3. Observar eficiencia de remoción
4. Generar gráficas para análisis

**Resultados esperados**:
- Dosis óptima: ~0.025-0.035 g/L
- Eficiencia máxima: 85-95%

### 2. 📊 Análisis de Velocidad de Sedimentación

**Objetivo**: Estudiar el efecto del gradiente G en la sedimentación

**Pasos**:
1. Fijar dosis de coagulante (0.025 g/L)
2. Variar caudal para cambiar G
3. Monitorear velocidad de sedimentación
4. Analizar relación G vs velocidad

**Resultados esperados**:
- G óptimo: 40-60 s⁻¹
- Velocidad sedimentación: 0.5-1.5 mm/s

### 3. 🌡️ Efecto de la Temperatura

**Objetivo**: Evaluar impacto de temperatura en eficiencia

**Pasos**:
1. Configurar parámetros estándar
2. Variar temperatura (15-30°C)
3. Comparar eficiencias
4. Documentar cambios en viscosidad

**Resultados esperados**:
- Mayor temperatura → Mayor eficiencia
- Diferencia: ~5-10% entre extremos

---

## 🔬 Experimentos Avanzados

### 4. 📈 Optimización Multi-parámetro

**Objetivo**: Encontrar condiciones óptimas operativas

**Variables a optimizar**:
- Dosis coagulante
- Caudal (tiempo retención)
- pH inicial
- Turbidez inicial

**Metodología**:
1. Diseño factorial de experimentos
2. Ejecutar múltiples simulaciones
3. Análisis estadístico de resultados
4. Superficie de respuesta

### 5. 🎛️ Control de Calidad del Efluente

**Objetivo**: Mantener calidad constante con agua variable

**Escenario**:
- Turbidez de entrada variable (20-100 NTU)
- Ajuste automático de parámetros
- Mantener efluente <5 NTU

**Estrategia**:
1. Monitoreo continuo
2. Ajuste de dosis según turbidez
3. Control de pH
4. Verificación de límites

---

## 💡 Casos de Estudio Reales

### Caso 1: Agua de Río con Alta Turbidez

**Características del agua**:
- Turbidez: 150 NTU
- pH: 6.8
- Temperatura: 22°C
- Color: 45 Pt-Co

**Tratamiento propuesto**:
- Dosis coagulante: 0.045 g/L
- Tiempo floculación: 15 min
- Carga superficial: 25 m/h

**Resultados simulados**:
- Eficiencia: 92%
- Turbidez final: 3.2 NTU
- Color final: 8 Pt-Co

### Caso 2: Agua Subterránea con Hierro

**Características del agua**:
- Turbidez: 25 NTU
- pH: 7.5
- Temperatura: 18°C
- Hierro: 2.5 mg/L

**Tratamiento propuesto**:
- Pre-oxidación (simulada)
- Dosis coagulante: 0.020 g/L
- pH ajustado: 7.2

**Resultados simulados**:
- Eficiencia: 88%
- Turbidez final: 1.8 NTU
- Hierro residual: <0.3 mg/L

---

## 🎓 Ejercicios para Estudiantes

### Ejercicio 1: Curva de Coagulación
**Tiempo estimado**: 30 minutos

1. Configurar agua con 60 NTU
2. Probar dosis: 0.01, 0.02, 0.03, 0.04, 0.05 g/L
3. Registrar eficiencias
4. Graficar curva dosis vs eficiencia
5. Identificar dosis óptima

### Ejercicio 2: Efecto del Tiempo de Retención
**Tiempo estimado**: 45 minutos

1. Fijar parámetros óptimos del Ejercicio 1
2. Variar caudal: 0.2, 0.3, 0.45, 0.6, 0.8 L/s
3. Calcular tiempos de retención
4. Analizar efecto en sedimentación
5. Determinar caudal óptimo

### Ejercicio 3: Análisis de Sensibilidad
**Tiempo estimado**: 60 minutos

1. Configurar condiciones base
2. Variar cada parámetro ±20%
3. Evaluar impacto en eficiencia
4. Ranking de sensibilidad
5. Recomendaciones operativas

---

## 📊 Interpretación de Gráficas

### Gráfica de Velocidad de Sedimentación

**Tendencias normales**:
- Inicio: Velocidad baja (partículas pequeñas)
- Medio: Aumento (formación flóculos)
- Final: Estabilización (flóculos maduros)

**Problemas comunes**:
- Velocidad muy baja: Poca coagulación
- Velocidad errática: G muy alto (rotura)
- Sin aumento: Dosis insuficiente

### Gráfica de Eficiencia

**Comportamiento esperado**:
- Aumento gradual hasta meseta
- Eficiencia >80% indica buen funcionamiento
- Oscilaciones <5% son normales

**Alertas**:
- Eficiencia <70%: Revisar parámetros
- Caída súbita: Problema operativo
- No estabilización: Tiempo insuficiente

### Gráfica de Turbidez

**Evolución típica**:
- Inicio: Turbidez alta (agua cruda)
- Descenso gradual por etapas
- Final: <5 NTU (agua tratada)

**Indicadores de calidad**:
- <1 NTU: Excelente
- 1-5 NTU: Aceptable
- >5 NTU: Requiere ajuste

---

## 🔧 Consejos de Operación

### ✅ Buenas Prácticas

1. **Inicio de simulación**:
   - Esperar estabilización (2-3 min)
   - Verificar parámetros iniciales
   - Monitorear tendencias

2. **Ajuste de parámetros**:
   - Cambios graduales (<20%)
   - Un parámetro a la vez
   - Esperar respuesta del sistema

3. **Interpretación de resultados**:
   - Considerar tiempo de retención
   - Evaluar tendencias, no valores puntuales
   - Comparar con referencias teóricas

### ⚠️ Errores Comunes

1. **Cambios muy rápidos**: El sistema necesita tiempo
2. **Parámetros extremos**: Fuera de rangos realistas
3. **No considerar interacciones**: Los parámetros se afectan mutuamente
4. **Interpretación prematura**: Esperar estabilización

---

## 📞 Soporte Técnico

### 🆘 ¿Cuándo contactar al equipo?

- Resultados inconsistentes con teoría
- Errores de software persistentes
- Dudas sobre interpretación
- Sugerencias de mejora

### 📧 Información a incluir

- Parámetros utilizados
- Capturas de pantalla
- Descripción del problema
- Resultados esperados vs obtenidos

**Contactos**:
- sharon.agudelo01@usa.edu.co
- Carlos.porras01@usa.edu.co
- juanesteban.marino01@usa.edu.co
- Guillermo.lopez02@usa.edu.co

---

¡Experimenta y aprende! 🧪💡