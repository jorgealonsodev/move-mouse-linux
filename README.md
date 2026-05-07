# Move Mouse Linux

Simula actividad de usuario para prevenir bloqueo de sesión.

Port para Linux del [Move Mouse](https://github.com/sw3103/movemouse) original de Windows.

## ¿Qué es?

Move Mouse Linux mueve el cursor del mouse a intervalos configurables para simular actividad del usuario. Esto previene que la sesión se bloquee o entre en suspensión durante tareas largas como descargas, compilaciones o renderizado.

## Características

- **15 direcciones de movimiento** del cursor (cuadrado, círculo, diagonal, etc.)
- **Intervalo configurable** con soporte de rango aleatorio
- **Auto-pausa** al detectar actividad real del usuario
- **Auto-reanudación** tras periodo de inactividad
- **Icono en bandeja del sistema** (AppIndicator3 / Gtk.StatusIcon)
- **Ventana de configuración** GTK con controles simples
- **Soporte X11** (primario, vía python-xlib + XTest)
- **Soporte Wayland** (fallback, vía ydotool)
- **Monitor de sesión** D-Bus: pausa al bloquear, reanuda al desbloquear
- **Configuración persistente** en JSON (`~/.config/move-mouse-linux/settings.json`)

## Instalación

### Flatpak (recomendado)

```bash
# Construir desde el manifiesto
flatpak-builder --user --install --force-clean build-dir \
  move-mouse-linux/flatpak/org.movemouse.MoveMouse.yml

# Ejecutar
flatpak run org.movemouse.MoveMouse
```

> **Nota:** Wayland/ydotool no funciona dentro de Flatpak por restricciones de sandbox. En entornos Wayland puros, usá el paquete .deb o pip.

### Paquete Debian (.deb)

```bash
# Instalar dependencias
sudo apt install python3-gi python3-xlib gir1.2-gtk-3.0 \
  gir1.2-appindicator3-0.1

# Construir el paquete
cd move-mouse-linux
dpkg-buildpackage -us -uc -b

# Instalar
sudo dpkg -i ../move-mouse_1.0.0-1_all.deb
```

### pip

```bash
pip install .

# O directamente desde el directorio del proyecto
pip install -e .
```

## Uso

```bash
# Modo GTK (por defecto, con bandeja de sistema)
move-mouse

# Modo CLI (sin interfaz gráfica)
move-mouse --no-gui

# Modo CLI con intervalo personalizado (en milisegundos)
move-mouse --no-gui --interval 60000

# Modo verbose
move-mouse -v
```

También podés ejecutarlo como módulo:

```bash
python -m move_mouse
```

### Inicio automático

El archivo `.desktop` incluido configura el inicio automático con GNOME. Si tu entorno no lo soporta, copiá el archivo manualmente:

```bash
cp data/org.movemouse.MoveMouse.desktop ~/.config/autostart/
```

## Estructura del proyecto

```
move_mouse/
├── core/           # Motor de estado, executor, detector de inactividad
├── actions/        # Acciones: mover, click, scroll, posición, sleep
├── backends/       # Backends de mouse: X11 (python-xlib), Wayland (ydotool)
├── models/         # Modelo de configuración y schedule (V2 stub)
├── ui/             # Interfaz GTK: aplicación, ventana, bandeja
├── services/       # Monitor de sesión D-Bus (logind)
└── main.py         # Punto de entrada CLI
```

## Requisitos

- Python 3.8+
- python-xlib (X11)
- pydbus (D-Bus)
- PyGObject + GTK 3 (UI)
- AppIndicator3 o libayatana-appindicator3 (bandeja)
- ydotool (opcional, Wayland)

## Créditos

- **Move Mouse original**: [sw3103/movemouse](https://github.com/sw3103/movemouse) — aplicación Windows de Chris Hunt
- **Port Linux**: basado en la arquitectura y funcionalidad del original

## Licencia

GPL-3.0 — ver archivo `LICENSE` para más detalles.
