# 🚀 Guía de Instalación Rápida

## ⚡ Instalación Express (5 minutos)

### 1️⃣ Verificar Python
```bash
python --version
# Debe mostrar Python 3.8 o superior
```

### 2️⃣ Descargar el proyecto
```bash
# Opción A: Clonar repositorio
git clone [URL_DEL_REPOSITORIO]
cd simulador-tratamiento-agua

# Opción B: Descargar ZIP y extraer
```

### 3️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ ¡Ejecutar!
```bash
python game_visualization.py
```

---

## 🔧 Instalación Detallada

### Para Windows 🪟

1. **Instalar Python**
   - Descargar desde [python.org](https://python.org)
   - ✅ Marcar "Add Python to PATH"

2. **Abrir Command Prompt**
   - `Win + R` → `cmd` → Enter

3. **Navegar al proyecto**
   ```cmd
   cd C:\ruta\al\proyecto
   ```

4. **Instalar dependencias**
   ```cmd
   pip install pygame numpy matplotlib pandas scipy
   ```

### Para macOS 🍎

1. **Instalar Python**
   ```bash
   # Con Homebrew (recomendado)
   brew install python
   
   # O descargar desde python.org
   ```

2. **Instalar dependencias**
   ```bash
   pip3 install pygame numpy matplotlib pandas scipy
   ```

### Para Linux 🐧

1. **Instalar Python y pip**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   ```

2. **Instalar dependencias del sistema**
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev python3-pygame
   
   # Luego instalar el resto
   pip3 install numpy matplotlib pandas scipy
   ```

---

## 🐛 Solución de Problemas Comunes

### ❌ "pygame not found"
```bash
pip install --upgrade pygame
```

### ❌ "No module named 'numpy'"
```bash
pip install numpy
```

### ❌ "Permission denied" (Linux/macOS)
```bash
pip install --user pygame numpy matplotlib pandas scipy
```

### ❌ Error de visualización
- Asegúrate de tener un entorno gráfico activo
- En servidores remotos, usa X11 forwarding

---

## ✅ Verificar Instalación

Ejecuta este comando para verificar que todo funciona:

```bash
python -c "import pygame, numpy, matplotlib; print('✅ Todo instalado correctamente!')"
```

---

## 🎯 Primeros Pasos

1. **Ejecutar el simulador**
   ```bash
   python game_visualization.py
   ```

2. **Probar las gráficas**
   ```bash
   python test_graphs.py
   ```

3. **Ver ejemplos**
   ```bash
   python example_usage.py
   ```

---

## 📞 ¿Necesitas Ayuda?

Si tienes problemas:

1. 📧 Contacta al equipo:
   - sharon.agudelo01@usa.edu.co
   - Carlos.porras01@usa.edu.co
   - juanesteban.marino01@usa.edu.co
   - Guillermo.lopez02@usa.edu.co

2. 🐛 Reporta el error con:
   - Tu sistema operativo
   - Versión de Python
   - Mensaje de error completo

¡Estamos aquí para ayudarte! 🤝