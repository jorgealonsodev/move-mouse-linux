"""Ejecutor de pipeline de acciones."""

import logging
from typing import List, Optional

from move_mouse.actions.base import ActionBase, ActionResult
from move_mouse.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class Executor:
    """Ejecuta una lista de acciones en orden respetando configuración de
    repetición y throttle.

    El executor recibe una lista de acciones y un tipo de disparador (trigger).
    Solo ejecuta las acciones cuyo ``trigger`` coincida con el proporcionado.
    Cada acción se ejecuta secuencialmente; si una acción es abortada por
    actividad de usuario y tiene ``abort_if_user_activity`` activo, el
    pipeline se detiene.
    """

    def __init__(
        self,
        actions: List[ActionBase],
        trigger: str = "interval",
        controller: Optional[MouseController] = None,
    ):
        self._actions = actions
        self._trigger = trigger
        self._controller = controller

    @property
    def actions(self) -> List[ActionBase]:
        return self._actions

    @property
    def trigger(self) -> str:
        return self._trigger

    @property
    def controller(self) -> Optional[MouseController]:
        return self._controller

    @controller.setter
    def controller(self, value: MouseController) -> None:
        self._controller = value

    def execute(self, controller: Optional[MouseController] = None) -> bool:
        """Ejecuta todas las acciones del pipeline.

        Args:
            controller: Controlador de mouse. Si no se proporciona, usa el
                configurado en el constructor.

        Returns:
            True si la ejecución fue abortada por actividad de usuario,
            False en caso contrario.
        """
        ctrl = controller or self._controller
        if ctrl is None:
            logger.error("No hay controlador de mouse disponible")
            return False

        aborted = False
        for action in self._actions:
            # Filtrar por trigger
            if action.trigger != self._trigger:
                continue

            if not action.is_enabled:
                logger.debug("Acción %s deshabilitada, saltando", action.id)
                continue

            if not action.can_execute():
                logger.debug("Acción %s no puede ejecutarse en este ciclo", action.id)
                continue

            logger.debug("Ejecutando acción: %s", action.id)
            try:
                result = action.execute(ctrl)
            except Exception as exc:
                logger.error("Error en acción %s: %s", action.id, exc)
                result = ActionResult(error=str(exc))



            if result.aborted:
                logger.info(
                    "Acción %s abortada por actividad de usuario", action.id
                )
                aborted = True
                # Marcar todas las acciones restantes como abortadas
                for remaining in self._actions:
                    if remaining is action:
                        continue
                    if remaining.trigger == self._trigger:
                        remaining.aborted = True
                break

        return aborted

    def reset_all_cycles(self) -> None:
        """Reinicia el conteo de ejecuciones de todas las acciones."""
        for action in self._actions:
            action.reset_cycle()

    def get_actions_for_trigger(self, trigger: str) -> List[ActionBase]:
        """Devuelve las acciones que coinciden con un trigger dado."""
        return [a for a in self._actions if a.trigger == trigger]
