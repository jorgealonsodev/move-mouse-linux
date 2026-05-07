"""Ícono de bandeja del sistema con soporte para AppIndicator y Gtk.StatusIcon."""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Intentar importar AppIndicator3; si no está disponible, usar Gtk.StatusIcon
try:
    import gi

    gi.require_version("Gtk", "3.0")
    # Preferir AyatanaAppIndicator3 si está disponible, sino AppIndicator3
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3

        _INDICATOR_AVAILABLE = True
        _INDICATOR_LIB = "AyatanaAppIndicator3"
    except ValueError:
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3

            _INDICATOR_AVAILABLE = True
            _INDICATOR_LIB = "AppIndicator3"
        except ValueError:
            _INDICATOR_AVAILABLE = False
            _INDICATOR_LIB = None
except ImportError:
    _INDICATOR_AVAILABLE = False
    _INDICATOR_LIB = None


class BandejaSistema:
    """Ícono de bandeja del sistema con menú contextual.

    Usa AppIndicator3 (o AyatanaAppIndicator3) si está disponible;
    de lo contrario, recurre a Gtk.StatusIcon.
    """

    def __init__(
        self,
        app_id: str = "org.movemouse.MoveMouse",
        icon_name: str = "input-mouse",
        titulo: str = "Move Mouse Linux",
    ):
        self._app_id = app_id
        self._icon_name = icon_name
        self._titulo = titulo
        self._indicador = None
        self._status_icon = None
        self._menu = None
        self._usando_appindicator = False

        # Callbacks
        self._on_iniciar: Optional[Callable[[], None]] = None
        self._on_detener: Optional[Callable[[], None]] = None
        self._on_mostrar_ventana: Optional[Callable[[], None]] = None
        self._on_acerca_de: Optional[Callable[[], None]] = None
        self._on_salir: Optional[Callable[[], None]] = None

        self._crear()

    # -- Propiedades de callbacks --

    @property
    def on_iniciar(self) -> Optional[Callable[[], None]]:
        return self._on_iniciar

    @on_iniciar.setter
    def on_iniciar(self, callback: Callable[[], None]) -> None:
        self._on_iniciar = callback

    @property
    def on_detener(self) -> Optional[Callable[[], None]]:
        return self._on_detener

    @on_detener.setter
    def on_detener(self, callback: Callable[[], None]) -> None:
        self._on_detener = callback

    @property
    def on_mostrar_ventana(self) -> Optional[Callable[[], None]]:
        return self._on_mostrar_ventana

    @on_mostrar_ventana.setter
    def on_mostrar_ventana(self, callback: Callable[[], None]) -> None:
        self._on_mostrar_ventana = callback

    @property
    def on_acerca_de(self) -> Optional[Callable[[], None]]:
        return self._on_acerca_de

    @on_acerca_de.setter
    def on_acerca_de(self, callback: Callable[[], None]) -> None:
        self._on_acerca_de = callback

    @property
    def on_salir(self) -> Optional[Callable[[], None]]:
        return self._on_salir

    @on_salir.setter
    def on_salir(self, callback: Callable[[], None]) -> None:
        self._on_salir = callback

    # -- Estado --

    @property
    def usando_appindicator(self) -> bool:
        return self._usando_appindicator

    @property
    def indicador(self):
        """Retorna el indicador o status_icon activo."""
        return self._indicador if self._usando_appindicator else self._status_icon

    # -- Creación --

    def _crear(self) -> None:
        if _INDICATOR_AVAILABLE:
            self._crear_con_appindicator()
        else:
            logger.info(
                "AppIndicator no disponible, usando Gtk.StatusIcon como respaldo"
            )
            self._crear_con_status_icon()

    def _crear_con_appindicator(self) -> None:
        """Crea el ícono usando AppIndicator3."""
        from gi.repository import Gtk

        self._indicador = AppIndicator3.Indicator.new(
            self._app_id, self._icon_name, AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self._indicador.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicador.set_title(self._titulo)

        self._menu = self._construir_menu(Gtk)
        self._indicador.set_menu(self._menu)
        self._usando_appindicator = True
        logger.debug("Bandeja creada con %s", _INDICATOR_LIB)

    def _crear_con_status_icon(self) -> None:
        """Crea el ícono usando Gtk.StatusIcon (respaldo)."""
        from gi.repository import Gtk

        self._status_icon = Gtk.StatusIcon()
        self._status_icon.set_from_icon_name(self._icon_name)
        self._status_icon.set_tooltip_text(self._titulo)
        self._status_icon.connect("activate", self._on_status_icon_activate)
        self._status_icon.connect("popup-menu", self._on_status_icon_popup)

        self._menu = self._construir_menu(Gtk)
        logger.debug("Bandeja creada con Gtk.StatusIcon")

    def _construir_menu(self, gtk_module) -> "gtk_module.Menu":
        """Construye el menú contextual con las opciones estándar."""
        menu = gtk_module.Menu()

        # Iniciar / Detener
        self._item_toggle = gtk_module.MenuItem(label="Iniciar")
        self._item_toggle.connect("activate", self._on_toggle_activate)
        menu.append(self._item_toggle)

        # Mostrar ventana
        item_ventana = gtk_module.MenuItem(label="Mostrar ventana")
        item_ventana.connect("activate", self._on_ventana_activate)
        menu.append(item_ventana)

        # Separador
        menu.append(gtk_module.SeparatorMenuItem())

        # Acerca de
        item_acerca = gtk_module.MenuItem(label="Acerca de")
        item_acerca.connect("activate", self._on_acerca_activate)
        menu.append(item_acerca)

        # Salir
        item_salir = gtk_module.MenuItem(label="Salir")
        item_salir.connect("activate", self._on_salir_activate)
        menu.append(item_salir)

        menu.show_all()
        return menu

    # -- Manejadores de eventos --

    def actualizar_estado(self, en_ejecucion: bool) -> None:
        """Actualiza el texto del botón toggle según el estado del motor."""
        if hasattr(self, "_item_toggle") and self._item_toggle is not None:
            if en_ejecucion:
                self._item_toggle.set_label("Detener")
            else:
                self._item_toggle.set_label("Iniciar")

    def _on_toggle_activate(self, widget) -> None:
        if self._on_iniciar and self._item_toggle.get_label() == "Iniciar":
            self._on_iniciar()
        elif self._on_detener and self._item_toggle.get_label() == "Detener":
            self._on_detener()

    def _on_ventana_activate(self, widget) -> None:
        if self._on_mostrar_ventana:
            self._on_mostrar_ventana()

    def _on_acerca_activate(self, widget) -> None:
        if self._on_acerca_de:
            self._on_acerca_de()

    def _on_salir_activate(self, widget) -> None:
        if self._on_salir:
            self._on_salir()

    def _on_status_icon_activate(self, icon) -> None:
        """Al hacer clic en StatusIcon, mostrar ventana."""
        if self._on_mostrar_ventana:
            self._on_mostrar_ventana()

    def _on_status_icon_popup(self, icon, button, activate_time) -> None:
        """Mostrar menú contextual en StatusIcon."""
        if self._menu:
            self._menu.popup(None, None, None, None, button, activate_time)
