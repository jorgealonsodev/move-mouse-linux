"""Tests para el módulo de bandeja del sistema."""

import sys
from unittest.mock import MagicMock, patch

import pytest


def _mock_gi_modules():
    """Configura mocks para gi y gi.repository en sys.modules."""
    mock_gi = MagicMock()
    mock_gtk = MagicMock()
    mock_appindicator = MagicMock()

    mock_repo = MagicMock()
    mock_repo.Gtk = mock_gtk
    mock_repo.AppIndicator3 = mock_appindicator
    mock_repo.AyatanaAppIndicator3 = mock_appindicator

    mock_gi.repository = mock_repo

    sys.modules["gi"] = mock_gi
    sys.modules["gi.repository"] = mock_repo
    return mock_gtk, mock_appindicator


def _limpiar_modulos():
    """Limpia los módulos cacheados para permitir reimport."""
    for mod in list(sys.modules.keys()):
        if mod.startswith("move_mouse.ui"):
            del sys.modules[mod]


class TestBandejaSistema:
    """Tests para BandejaSistema con mocks de GTK."""

    def setup_method(self):
        _limpiar_modulos()

    def teardown_method(self):
        _limpiar_modulos()
        for mod in ["gi", "gi.repository"]:
            sys.modules.pop(mod, None)

    def _crear_bandeja_appindicator(self):
        """Crea bandeja con AppIndicator disponible."""
        mock_gtk, mock_appindicator = _mock_gi_modules()

        # Configurar AppIndicator
        mock_indicator = MagicMock()
        mock_appindicator.Indicator.new.return_value = mock_indicator
        mock_appindicator.IndicatorCategory.SYSTEM_SERVICES = 0
        mock_appindicator.IndicatorStatus.ACTIVE = 1

        # Configurar GTK widgets
        mock_menu = MagicMock()
        mock_gtk.Menu.return_value = mock_menu
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Iniciar"
        mock_gtk.MenuItem.return_value = mock_item
        mock_gtk.SeparatorMenuItem.return_value = MagicMock()

        # Patchear las variables del módulo tray
        import move_mouse.ui.tray as tray_mod

        tray_mod._INDICATOR_AVAILABLE = True
        tray_mod._INDICATOR_LIB = "AppIndicator3"
        tray_mod.AppIndicator3 = mock_appindicator

        from move_mouse.ui.tray import BandejaSistema

        return BandejaSistema(), mock_gtk, mock_appindicator, mock_indicator

    def _crear_bandeja_status_icon(self):
        """Crea bandeja con StatusIcon (fallback)."""
        mock_gtk, mock_appindicator = _mock_gi_modules()

        mock_status_icon = MagicMock()
        mock_gtk.StatusIcon.return_value = mock_status_icon
        mock_menu = MagicMock()
        mock_gtk.Menu.return_value = mock_menu
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Iniciar"
        mock_gtk.MenuItem.return_value = mock_item
        mock_gtk.SeparatorMenuItem.return_value = MagicMock()

        import move_mouse.ui.tray as tray_mod

        tray_mod._INDICATOR_AVAILABLE = False
        tray_mod._INDICATOR_LIB = None

        from move_mouse.ui.tray import BandejaSistema

        return BandejaSistema(), mock_gtk, mock_status_icon

    def test_creacion_con_appindicator(self):
        """La bandeja se crea usando AppIndicator cuando está disponible."""
        bandeja, mock_gtk, mock_appindicator, mock_indicator = (
            self._crear_bandeja_appindicator()
        )

        assert bandeja.usando_appindicator is True
        mock_appindicator.Indicator.new.assert_called_once()
        mock_indicator.set_status.assert_called_once()
        mock_indicator.set_menu.assert_called_once()

    def test_creacion_con_status_icon_fallback(self):
        """La bandeja usa Gtk.StatusIcon cuando AppIndicator no está disponible."""
        bandeja, mock_gtk, mock_status_icon = self._crear_bandeja_status_icon()

        assert bandeja.usando_appindicator is False
        mock_gtk.StatusIcon.assert_called_once()
        mock_status_icon.set_from_icon_name.assert_called_once()
        mock_status_icon.set_tooltip_text.assert_called_once()

    def test_callbacks_se_asignan(self):
        """Los callbacks se pueden asignar y leer."""
        bandeja, _, _ = self._crear_bandeja_status_icon()

        callback_iniciar = MagicMock()
        callback_detener = MagicMock()
        callback_mostrar = MagicMock()
        callback_salir = MagicMock()

        bandeja.on_iniciar = callback_iniciar
        bandeja.on_detener = callback_detener
        bandeja.on_mostrar_ventana = callback_mostrar
        bandeja.on_salir = callback_salir

        assert bandeja.on_iniciar is callback_iniciar
        assert bandeja.on_detener is callback_detener
        assert bandeja.on_mostrar_ventana is callback_mostrar
        assert bandeja.on_salir is callback_salir

    def test_actualizar_estado_cambia_etiqueta(self):
        """actualizar_estado cambia la etiqueta del toggle."""
        bandeja, mock_gtk, mock_status_icon = self._crear_bandeja_status_icon()
        mock_item = MagicMock()
        bandeja._item_toggle = mock_item

        bandeja.actualizar_estado(True)
        mock_item.set_label.assert_called_with("Detener")

        bandeja.actualizar_estado(False)
        mock_item.set_label.assert_called_with("Iniciar")

    def test_toggle_iniciar_ejecuta_callback(self):
        """Al hacer toggle con label 'Iniciar', ejecuta on_iniciar."""
        bandeja, mock_gtk, mock_status_icon = self._crear_bandeja_status_icon()
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Iniciar"
        bandeja._item_toggle = mock_item
        callback = MagicMock()
        bandeja.on_iniciar = callback

        bandeja._on_toggle_activate(None)

        callback.assert_called_once()

    def test_toggle_detener_ejecuta_callback(self):
        """Al hacer toggle con label 'Detener', ejecuta on_detener."""
        bandeja, mock_gtk, mock_status_icon = self._crear_bandeja_status_icon()
        mock_item = MagicMock()
        mock_item.get_label.return_value = "Detener"
        bandeja._item_toggle = mock_item
        callback = MagicMock()
        bandeja.on_detener = callback

        bandeja._on_toggle_activate(None)

        callback.assert_called_once()

    def test_menu_items_se_conectan(self):
        """Los items del menú se conectan a sus handlers."""
        bandeja, mock_gtk, mock_status_icon = self._crear_bandeja_status_icon()

        # Verificar que se crearon varios MenuItem
        assert mock_gtk.MenuItem.call_count >= 3
        mock_gtk.Menu.return_value.show_all.assert_called_once()
