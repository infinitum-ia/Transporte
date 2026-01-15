"""
Context Builder - Versión Simplificada
Solo formateo de datos y alertas. Sin LLM ni análisis emocional.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import locale

logger = logging.getLogger(__name__)


class ContextBuilderAgent:
    """
    Construcción de contexto simplificada.

    Responsabilidades:
    1. Formatear fechas del Excel
    2. Generar alertas críticas

    NO hace llamadas LLM. El prompt ya tiene las instrucciones necesarias.
    """

    def __init__(self, base_path: Optional[str] = None):
        """Inicializa el Context Builder."""
        # Configurar locale español para formato de fechas
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
            except:
                logger.warning("No se pudo configurar locale español")

        logger.info("ContextBuilderAgent inicializado (versión simplificada)")

    def build_context(
        self,
        state: Dict[str, Any],
        last_user_message: str,
        current_phase: str
    ) -> Dict[str, Any]:
        """
        Construye contexto para el prompt.

        Args:
            state: Estado de la conversación
            last_user_message: Último mensaje del usuario
            current_phase: Fase actual

        Returns:
            Dict con contexto formateado y alertas
        """
        logger.info(f"[CONTEXT_BUILDER] Construyendo contexto para fase: {current_phase}")

        # 1. Formatear datos del Excel (fechas, etc.)
        contexto_excel = self._format_excel_context(state)

        # 2. Generar alertas críticas
        alertas = self._generate_alerts(state, current_phase)

        return {
            "contexto_excel": contexto_excel,
            "alertas": alertas,
            # Campos vacíos por compatibilidad
            "politicas_relevantes": [],
            "casos_similares": [],
            "analisis_emocional": None
        }

    def _format_excel_context(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Formatea datos del Excel, especialmente fechas.

        Args:
            state: Estado de la conversación

        Returns:
            Dict con datos formateados
        """
        contexto = {}

        # Nombre del paciente
        if state.get('patient_full_name'):
            contexto['patient_name'] = state['patient_full_name']

        # Tipo de servicio
        if state.get('service_type'):
            contexto['service_type'] = state['service_type']

        # Formatear fecha con día de la semana
        appointment_date = state.get('appointment_date', '')
        if appointment_date:
            contexto['appointment_date_full'] = self._format_date(appointment_date)
            contexto['appointment_date_raw'] = appointment_date

        # Hora
        if state.get('appointment_time'):
            contexto['appointment_time'] = state['appointment_time']

        # Dirección
        if state.get('pickup_address'):
            contexto['pickup_address'] = state['pickup_address']

        return contexto

    def _format_date(self, date_str: str) -> str:
        """
        Formatea fecha a formato legible con día de semana.

        Args:
            date_str: Fecha en formato DD/MM/YYYY o YYYY-MM-DD

        Returns:
            Fecha formateada (ej: "mañana, MARTES 15 de enero")
        """
        try:
            # Manejar múltiples fechas separadas por coma
            dates_list = [d.strip() for d in date_str.split(',')]
            today = datetime.now().date()
            parsed_dates = []

            for ds in dates_list:
                try:
                    if '-' in ds:
                        date_obj = datetime.strptime(ds, '%Y-%m-%d')
                    else:
                        date_obj = datetime.strptime(ds, '%d/%m/%Y')
                    parsed_dates.append(date_obj)
                except Exception:
                    continue

            if not parsed_dates:
                return date_str

            # Seleccionar próxima fecha futura
            future_dates = [d for d in parsed_dates if d.date() >= today]
            selected_date = future_dates[0] if future_dates else parsed_dates[0]

            # Día de la semana y mes en español sin depender del locale del sistema
            day_names_es = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
            month_names_es = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            day_name = day_names_es[selected_date.weekday()]
            date_formatted = f"{selected_date.day:02d} de {month_names_es[selected_date.month - 1]}"

            # Relativo (hoy, mañana, etc.)
            diff_days = (selected_date.date() - today).days
            if diff_days == 0:
                result = f"hoy {day_name} {date_formatted}"
            elif diff_days == 1:
                result = f"mañana {day_name} {date_formatted}"
            elif diff_days == 2:
                result = f"pasado mañana {day_name} {date_formatted}"
            else:
                result = f"{day_name} {date_formatted}"

            if len(parsed_dates) > 1:
                result += f" (y {len(parsed_dates)-1} fecha{'s' if len(parsed_dates)-1 > 1 else ''} más)"

            return result

        except Exception as e:
            logger.warning(f"Error formateando fecha '{date_str}': {e}")
            return date_str

    def _generate_alerts(self, state: Dict[str, Any], phase: str) -> List[str]:
        """
        Genera alertas críticas basadas en el estado.

        Args:
            state: Estado de la conversación
            phase: Fase actual

        Returns:
            Lista de alertas
        """
        alertas = []

        # Alerta: falta fecha en fases de confirmación
        if phase in ["OUTBOUND_SERVICE_CONFIRMATION", "SERVICE_COORDINATION"]:
            if not state.get('appointment_date'):
                alertas.append("FALTA FECHA - No puedes confirmar sin fecha")

        # Alerta: validar edad de familiares menores
        contact_rel = (state.get('contact_relationship') or '').lower()
        contact_age = state.get('contact_age')

        if contact_rel in ['hijo', 'hija', 'nieto', 'nieta']:
            if not contact_age:
                alertas.append("VALIDAR EDAD - Familiar es hijo/nieto, pregunta edad antes de dar info")
            elif int(contact_age) < 18:
                alertas.append("MENOR DE EDAD - NO dar información, solicitar adulto")

        return alertas


# Factory function
def get_context_builder() -> ContextBuilderAgent:
    """Factory para obtener instancia de ContextBuilderAgent."""
    return ContextBuilderAgent()
