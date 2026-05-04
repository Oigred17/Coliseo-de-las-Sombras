# Coliseo de las Sombras

Un juego de acción y plataforma hecho con **Python** y **Pygame-CE**. 

Controla un guerrero en una arena oscura, lucha contra enemigos y jefes épicos usando tu espada, dash, parry y más habilidades.

---

## Requisitos

- **Python 3.7+**
- **pip** (gestor de paquetes de Python)

---

## Instalación y Ejecución

### 1. **Clonar o descargar el proyecto**

Si aún no tienes el proyecto, clónalo o descárgalo.

### 2. **Abrir terminal en la carpeta del proyecto**

```bash
cd Coliseo-de-las-Sombras
```

### 3. **Crear un entorno virtual (recomendado)**

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

### 5. **Ejecutar el juego**

```bash
python main.py
```

¡El juego debería iniciar!

> [!TIP]
> Si prefieres evitar conflictos con otras versiones de pygame, siempre usa un entorno virtual. Es la mejor práctica en desarrollo Python.

---

## Controles

### Teclado
| Acción | Tecla |
|--------|-------|
| Mover izquierda | `A` |
| Mover derecha | `D` |
| Saltar | `Espacio` |
| Atacar | `J` |
| Dash | `K` |
| Parry | `U` |

### Mando (Gamepad)
- **Joystick Izquierdo**: Movimiento
- **Botones**: Atacar, saltar, dash, parry (según configuración)

---

## Estructura del Proyecto

```
Coliseo-de-las-Sombras/
├── main.py                    # Archivo principal del juego
├── player.py                  # Lógica del jugador
├── enemies.py                 # Enemigos y jefes
├── settings.py                # Configuración general
├── spritesheet.py             # Cargador de sprites
├── hud.py                     # Interfaz de usuario
├── tutorial.py                # Tutorial del juego
├── requirements.txt           # Dependencias Python
├── Sprites/                   # Sprites de personajes y enemigos
├── Efectos de sonido/         # Música y efectos de sonido
└── README.md                  # Este archivo
```

---

## Solución de problemas

> [!WARNING]
> Asegúrate de tener la carpeta `Sprites/` y `Efectos de sonido/` en el directorio del proyecto. Sin estos recursos, el juego no funcionará correctamente.

### Error: "No module named 'pygame'"
```bash
pip install pygame-ce
```

### Error: "No se pudieron cargar los sonidos"
Asegúrate de que los archivos de audio estén en la carpeta `Efectos de sonido/`

### El juego va muy lento
Reduce la configuración gráfica o intenta ejecutarlo en una máquina más potente.

---

## Notas

> [!NOTE]
> El juego está optimizado para ejecutarse a 60 FPS. Si experimentas lag, verifica que tu máquina cumpla con los requisitos mínimos.

- El juego requiere que todos los assets (sprites, sonidos) estén en sus carpetas respectivas
- Ajusta la configuración en `settings.py` si necesitas cambiar resolución, dificultad, etc.
- Compatible con teclado y mando con vibración

---

## Disfruta el juego y que gane el mejor guerrero del Coliseo de las Sombras!

