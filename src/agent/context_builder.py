"""
Context Builder Agent - LLM-based context analysis for dynamic prompt construction

REFACTORED VERSION:
- Uses LLM to identify relevant policies and cases (no keyword matching)
- Uses ResourceLoader for centralized resource access
- Clean, focused responsibility
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import locale
from langchain_openai import ChatOpenAI
from src.agent.resources import get_resource_loader

logger = logging.getLogger(__name__)


class ContextBuilderAgent:
    """
    LLM-powered agent for building dynamic context for the main conversation agent.

    Responsibilities:
    1. Analyze user message and conversation state
    2. Use LLM to identify relevant policies (not keyword matching)
    3. Use LLM to identify relevant cases (not keyword matching)
    4. Format date/time from Excel data
    5. Generate critical alerts

    This agent is LIGHTWEIGHT and FAST - it does one thing well.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the Context Builder.

        Args:
            base_path: Project base path (optional, auto-detected if None)
        """
        # Load resources using centralized loader
        self.resource_loader = get_resource_loader()

        # Initialize LLM for context analysis
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set, LLM context analysis will fail")

        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.0,  # Deterministic for context selection
            api_key=openai_api_key
        )

        # Configure locale for Spanish date formatting
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
            except:
                logger.warning("Could not set Spanish locale for date formatting")

        logger.info("ContextBuilderAgent initialized with LLM-based analysis")

    def build_context(
        self,
        state: Dict[str, Any],
        last_user_message: str,
        current_phase: str
    ) -> Dict[str, Any]:
        """
        Build dynamic context for injection into the main agent's prompt.

        OPTIMIZED: Combines policy/case identification + emotional analysis in ONE LLM call.
        Reduces from 3 LLM calls to 1 LLM call (66% cost reduction).

        Args:
            state: Current conversation state
            last_user_message: Last message from user
            current_phase: Current conversation phase

        Returns:
            Dict with sections to inject:
            {
                "politicas_relevantes": [list of relevant policies],
                "casos_similares": [list of relevant cases],
                "contexto_excel": {formatted Excel data},
                "alertas": [critical alerts for agent],
                "analisis_emocional": {sentiment, conflict_level, personality_mode, ...}
            }
        """
        logger.info(f"[CONTEXT_BUILDER] Building context for phase: {current_phase}")
        logger.info(f"[CONTEXT_BUILDER] User message: '{last_user_message[:80]}...'")

        # 1. OPTIMIZED: Identify policies + cases + emotional analysis in ONE LLM call
        # For OUTBOUND_GREETING, use defaults (no LLM needed for first greeting)
        if current_phase == "OUTBOUND_GREETING" and state.get("turn_count", 0) == 0:
            politicas_relevantes = self._get_default_outbound_greeting_policies()
            casos_similares = self._get_default_outbound_greeting_cases()
            analisis_emocional = {
                "sentiment": "Neutro",
                "conflict_level": "Bajo",
                "personality_mode": "Balanceado",
                "emotional_validation_required": False,
                "sarcasm_detected": False,
                "ambiguity_detected": False
            }
            logger.info(f"[CONTEXT_BUILDER] Using defaults for OUTBOUND_GREETING turn 0")
        else:
            # OPTIMIZED: ONE LLM call does EVERYTHING
            unified_analysis = self._unified_context_analysis_llm(
                last_user_message, current_phase, state
            )
            politicas_relevantes = unified_analysis["politicas_relevantes"]
            casos_similares = unified_analysis["casos_similares"]
            analisis_emocional = unified_analysis["analisis_emocional"]

        # 2. Format Excel context (dates, patient info, etc.) - no LLM
        contexto_excel = self._format_excel_context(state)

        # 3. Generate critical alerts - no LLM
        alertas = self._generate_alerts(state, current_phase)

        result = {
            "politicas_relevantes": politicas_relevantes,
            "casos_similares": casos_similares,
            "contexto_excel": contexto_excel,
            "alertas": alertas,
            "analisis_emocional": analisis_emocional  # NEW
        }

        logger.info(f"[CONTEXT_BUILDER] Context built: {len(politicas_relevantes)} policies, "
                   f"{len(casos_similares)} cases, {len(alertas)} alerts, "
                   f"sentiment={analisis_emocional['sentiment']}")

        return result

    def _unified_context_analysis_llm(
        self,
        message: str,
        phase: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        OPTIMIZED: Use ONE LLM call to analyze EVERYTHING:
        1. Identify 2 relevant policies
        2. Identify 1 relevant case
        3. Analyze emotional context (sentiment, conflict, personality mode)

        This replaces 3 separate LLM calls with 1 unified call (66% cost reduction).

        Args:
            message: User's message
            phase: Current conversation phase
            state: Conversation state

        Returns:
            Dict with: {
                "politicas_relevantes": [policy texts],
                "casos_similares": [case texts],
                "analisis_emocional": {sentiment, conflict_level, ...}
            }
        """
        logger.info("[CONTEXT_BUILDER] Running UNIFIED context analysis (1 LLM call)...")

        # Get all available resources
        all_policies = self.resource_loader.get_all_politicas()
        all_cases = self.resource_loader.get_all_casos()

        if not all_policies or not all_cases:
            logger.warning("No policies or cases loaded, returning empty analysis")
            return {
                "politicas_relevantes": [],
                "casos_similares": [],
                "analisis_emocional": {
                    "sentiment": "Neutro",
                    "conflict_level": "Bajo",
                    "personality_mode": "Balanceado",
                    "emotional_validation_required": False,
                    "sarcasm_detected": False,
                    "ambiguity_detected": False
                }
            }

        # Build policy and case lists
        policy_titles = list(all_policies.keys())
        case_titles = list(all_cases.keys())
        policy_list_str = "\n".join([f"{i+1}. {title}" for i, title in enumerate(policy_titles)])
        case_list_str = "\n".join([f"{i+1}. {title}" for i, title in enumerate(case_titles)])

        # Get emotional history
        emotional_memory = state.get("emotional_memory", [])
        emotional_history_str = ""
        if emotional_memory:
            recent_emotions = emotional_memory[-3:]  # Last 3 turns
            emotional_history_str = "\n".join([
                f"- Turno {e['turn']}: {e['sentiment']} (Conflicto: {e['conflict_level']})"
                for e in recent_emotions
            ])
        else:
            emotional_history_str = "(Sin historial previo)"

        # Build unified prompt
        prompt = f"""Eres un analista experto en atención al cliente. Analiza el siguiente contexto de conversación.

FASE ACTUAL: {phase}
MENSAJE DEL USUARIO: "{message}"
ESTADO: Paciente={state.get('patient_full_name', 'N/A')}, Servicio={state.get('service_type', 'N/A')}

HISTORIAL EMOCIONAL RECIENTE:
{emotional_history_str}

═══════════════════════════════════════════════════════════════

TAREA 1: POLÍTICAS RELEVANTES
Selecciona MÁXIMO 2 NÚMEROS de las políticas MÁS relevantes para este contexto.

POLÍTICAS DISPONIBLES:
{policy_list_str}

═══════════════════════════════════════════════════════════════

TAREA 2: CASOS SIMILARES
Selecciona SOLO el NÚMERO del caso MÁS relevante (máximo 1).

CASOS DISPONIBLES:
{case_list_str}

═══════════════════════════════════════════════════════════════

TAREA 3: ANÁLISIS EMOCIONAL
Analiza el mensaje del usuario y clasifica:

1. **Sentimiento**: Clasifica en una de estas categorías:
   - Frustración: Usuario molesto, enojado, impaciente
   - Incertidumbre: Usuario confundido, inseguro, con dudas
   - Neutro: Tono normal, sin emociones marcadas
   - Euforia: Usuario muy contento, agradecido, positivo

2. **Nivel de Conflicto**: Evalúa la intensidad:
   - Bajo: Consulta simple, sin problema grave
   - Medio: Problema que requiere atención, pero manejable
   - Alto: Problema grave, usuario muy molesto o urgente

3. **Modo de Personalidad Sugerido**:
   - Simplificado: Si hay confusión repetida o usuario pregunta "¿Cómo?" repetidamente
   - Técnico: Si el usuario pide detalles específicos, datos precisos
   - Balanceado: Conversación estándar (default)

4. **Validación Emocional Requerida**: Si hay frustración o enojo, el agente debe validar
   emoción ANTES de dar datos técnicos.

5. **Expresiones no literales**:
   - Sarcasmo: ¿El usuario usa sarcasmo o ironía?
   - Ambigüedad: ¿El mensaje es ambiguo o poco claro?

═══════════════════════════════════════════════════════════════

RESPONDE SOLO con un JSON con esta estructura EXACTA:
{{
  "relevant_policy_numbers": [1, 3],
  "relevant_case_numbers": [2],
  "sentiment": "Frustración|Incertidumbre|Neutro|Euforia",
  "conflict_level": "Bajo|Medio|Alto",
  "personality_mode": "Balanceado|Simplificado|Técnico",
  "emotional_validation_required": true/false,
  "sarcasm_detected": true/false,
  "ambiguity_detected": true/false
}}

Si ninguna política/caso es relevante, devuelve listas vacías: {{"relevant_policy_numbers": [], "relevant_case_numbers": []}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            result = json.loads(content)

            # Extract policies
            selected_policy_numbers = result.get("relevant_policy_numbers", [])
            politicas_relevantes = []
            for num in selected_policy_numbers:
                if 1 <= num <= len(policy_titles):
                    policy_title = policy_titles[num - 1]
                    politicas_relevantes.append(all_policies[policy_title])

            # Extract cases (limit to first 15 lines)
            selected_case_numbers = result.get("relevant_case_numbers", [])
            casos_similares = []
            for num in selected_case_numbers:
                if 1 <= num <= len(case_titles):
                    case_title = case_titles[num - 1]
                    case_text = all_cases[case_title]
                    case_lines = case_text.split('\n')[:15]
                    casos_similares.append('\n'.join(case_lines))

            # Extract emotional analysis
            analisis_emocional = {
                "sentiment": result.get("sentiment", "Neutro"),
                "conflict_level": result.get("conflict_level", "Bajo"),
                "personality_mode": result.get("personality_mode", "Balanceado"),
                "emotional_validation_required": result.get("emotional_validation_required", False),
                "sarcasm_detected": result.get("sarcasm_detected", False),
                "ambiguity_detected": result.get("ambiguity_detected", False)
            }

            logger.info(f"[CONTEXT_BUILDER] UNIFIED analysis complete: "
                       f"{len(politicas_relevantes)} policies, "
                       f"{len(casos_similares)} cases, "
                       f"sentiment={analisis_emocional['sentiment']}, "
                       f"conflict={analisis_emocional['conflict_level']}")

            return {
                "politicas_relevantes": politicas_relevantes,
                "casos_similares": casos_similares,
                "analisis_emocional": analisis_emocional
            }

        except Exception as e:
            logger.error(f"[CONTEXT_BUILDER] Error in unified analysis: {e}", exc_info=True)
            # Fallback: return safe defaults
            return {
                "politicas_relevantes": [],
                "casos_similares": [],
                "analisis_emocional": {
                    "sentiment": "Neutro",
                    "conflict_level": "Bajo",
                    "personality_mode": "Balanceado",
                    "emotional_validation_required": False,
                    "sarcasm_detected": False,
                    "ambiguity_detected": False
                }
            }

    def _identify_relevant_policies_llm(
        self,
        message: str,
        phase: str,
        state: Dict[str, Any]
    ) -> List[str]:
        """
        Use LLM to identify relevant policies based on context.

        This replaces keyword matching with intelligent analysis.

        Args:
            message: User's message
            phase: Current conversation phase
            state: Conversation state

        Returns:
            List of relevant policy texts
        """
        logger.info("[CONTEXT_BUILDER] Analyzing policies with LLM...")

        # Get all available policies
        all_policies = self.resource_loader.get_all_politicas()

        if not all_policies:
            logger.warning("No policies loaded")
            return []

        # Build LLM prompt for policy selection
        policy_titles = list(all_policies.keys())
        policy_list_str = "\n".join([f"{i+1}. {title}" for i, title in enumerate(policy_titles)])

        prompt = f"""Eres un asistente experto en identificar políticas relevantes.

Dado el siguiente contexto de conversación, identifica qué políticas son relevantes.

FASE ACTUAL: {phase}
MENSAJE DEL USUARIO: "{message}"
ESTADO: Paciente={state.get('patient_full_name', 'N/A')}, Servicio={state.get('service_type', 'N/A')}, Dirección={state.get('pickup_address', 'N/A')}

POLÍTICAS DISPONIBLES:
{policy_list_str}

TAREA: Selecciona MÁXIMO 2 NÚMEROS de las políticas MÁS relevantes para este contexto.
Prioriza calidad sobre cantidad - solo las CRÍTICAS para la situación actual.

Responde SOLO con un JSON con esta estructura:
{{
  "relevant_policy_numbers": [1, 3]
}}

Si ninguna política es relevante, devuelve lista vacía: {{"relevant_policy_numbers": []}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            result = json.loads(content)
            selected_numbers = result.get("relevant_policy_numbers", [])

            # Get policy texts
            relevant_policies = []
            for num in selected_numbers:
                if 1 <= num <= len(policy_titles):
                    policy_title = policy_titles[num - 1]
                    relevant_policies.append(all_policies[policy_title])

            logger.info(f"[CONTEXT_BUILDER] LLM selected {len(relevant_policies)} relevant policies")
            return relevant_policies

        except Exception as e:
            logger.error(f"[CONTEXT_BUILDER] Error in LLM policy selection: {e}", exc_info=True)
            # Fallback: return empty list
            return []

    def _identify_relevant_cases_llm(
        self,
        message: str,
        phase: str,
        state: Dict[str, Any]
    ) -> List[str]:
        """
        Use LLM to identify relevant cases based on context.

        This replaces keyword matching with intelligent analysis.

        Args:
            message: User's message
            phase: Current conversation phase
            state: Conversation state

        Returns:
            List of relevant case texts
        """
        logger.info("[CONTEXT_BUILDER] Analyzing cases with LLM...")

        # Get all available cases
        all_cases = self.resource_loader.get_all_casos()

        if not all_cases:
            logger.warning("No cases loaded")
            return []

        # Build LLM prompt for case selection
        case_titles = list(all_cases.keys())
        case_list_str = "\n".join([f"{i+1}. {title}" for i, title in enumerate(case_titles)])

        prompt = f"""Eres un asistente experto en identificar casos similares.

Dado el siguiente contexto de conversación, identifica qué casos similares son relevantes.

FASE ACTUAL: {phase}
MENSAJE DEL USUARIO: "{message}"
ESTADO: Paciente={state.get('patient_full_name', 'N/A')}, Servicio={state.get('service_type', 'N/A')}

CASOS DISPONIBLES:
{case_list_str}

TAREA: Selecciona SOLO el NÚMERO del caso MÁS relevante (máximo 1).
Prioriza calidad sobre cantidad - solo el caso que mejor ejemplifique la situación actual.

Responde SOLO con un JSON con esta estructura:
{{
  "relevant_case_numbers": [2]
}}

Si ningún caso es relevante, devuelve lista vacía: {{"relevant_case_numbers": []}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            result = json.loads(content)
            selected_numbers = result.get("relevant_case_numbers", [])

            # Get case texts (limit to first 15 lines each)
            relevant_cases = []
            for num in selected_numbers:
                if 1 <= num <= len(case_titles):
                    case_title = case_titles[num - 1]
                    case_text = all_cases[case_title]
                    # Limit to 15 lines to avoid context bloat
                    case_lines = case_text.split('\n')[:15]
                    relevant_cases.append('\n'.join(case_lines))

            logger.info(f"[CONTEXT_BUILDER] LLM selected {len(relevant_cases)} relevant cases")
            return relevant_cases

        except Exception as e:
            logger.error(f"[CONTEXT_BUILDER] Error in LLM case selection: {e}", exc_info=True)
            # Fallback: return empty list
            return []

    def _format_excel_context(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Format Excel context with complete date formatting.

        CRITICAL: Includes day of week + full date + time

        Args:
            state: Conversation state

        Returns:
            Dict with formatted Excel data
        """
        logger.info("[CONTEXT_BUILDER] Formatting Excel context...")

        contexto = {}

        # Patient name
        patient_name = state.get('patient_full_name', '')
        if patient_name:
            contexto['patient_name'] = patient_name

        # Service type
        service_type = state.get('service_type', '')
        if service_type:
            contexto['service_type'] = service_type

        # Date with day of week
        appointment_date = state.get('appointment_date', '')
        if appointment_date:
            try:
                # Handle multiple dates separated by commas (e.g., "07/01/2025,08/01/2025")
                dates_list = [d.strip() for d in appointment_date.split(',')]

                # Parse dates and find the next future date (or first date if all are future)
                today = datetime.now().date()
                parsed_dates = []

                for date_str in dates_list:
                    try:
                        if '-' in date_str:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        else:
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        parsed_dates.append(date_obj)
                    except Exception as e:
                        logger.warning(f"[CONTEXT_BUILDER] Could not parse date '{date_str}': {e}")

                if not parsed_dates:
                    raise ValueError(f"No valid dates found in '{appointment_date}'")

                # Select the next future date or first date
                future_dates = [d for d in parsed_dates if d.date() >= today]
                selected_date = future_dates[0] if future_dates else parsed_dates[0]

                # Get day name in Spanish
                day_name = selected_date.strftime('%A').upper()  # LUNES, MARTES, etc.
                date_formatted = selected_date.strftime('%d de %B')  # 15 de octubre

                # Determine relative date
                diff_days = (selected_date.date() - today).days

                if diff_days == 0:
                    relative = "hoy"
                elif diff_days == 1:
                    relative = "mañana"
                elif diff_days == 2:
                    relative = "pasado mañana"
                else:
                    relative = f"este {day_name}"

                # Build formatted date with indicator if multiple dates
                date_text = f"{relative}, {day_name} {date_formatted}"
                if len(parsed_dates) > 1:
                    date_text += f" (y {len(parsed_dates)-1} fecha{'s' if len(parsed_dates)-1 > 1 else ''} más)"

                contexto['appointment_date_full'] = date_text
                contexto['appointment_date_raw'] = appointment_date
                logger.info(f"[CONTEXT_BUILDER] Date formatted: '{contexto['appointment_date_full']}' from {len(parsed_dates)} date(s)")

            except Exception as e:
                logger.error(f"[CONTEXT_BUILDER] Error parsing date {appointment_date}: {e}")
                contexto['appointment_date_full'] = appointment_date

        # Time
        appointment_time = state.get('appointment_time', '')
        if appointment_time:
            contexto['appointment_time'] = appointment_time

        # Pickup address
        pickup_address = state.get('pickup_address', '')
        if pickup_address:
            contexto['pickup_address'] = pickup_address

        return contexto

    def _generate_alerts(self, state: Dict[str, Any], phase: str) -> List[str]:
        """
        Generate critical alerts for the agent.

        Args:
            state: Conversation state
            phase: Current phase

        Returns:
            List of alert strings
        """
        alertas = []

        # Alert if missing date
        if not state.get('appointment_date'):
            alertas.append("⚠️ FALTA FECHA DE LA CITA - No puedes confirmar sin fecha completa")

        # Alert for underage family member
        contact_rel = state.get('contact_relationship') or ''
        contact_rel_lower = contact_rel.lower() if contact_rel else ''
        contact_age = state.get('contact_age')

        if any(rel in contact_rel_lower for rel in ['hijo', 'hija', 'nieto', 'nieta']):
            if not contact_age:
                alertas.append("🚨 VALIDACIÓN PENDIENTE - Familiar es hijo/nieto: DEBES preguntar EDAD antes de dar información sensible")
            elif contact_age and int(contact_age) < 18:
                alertas.append("⛔ MENOR DE EDAD - NO puedes dar información. Solicita adulto autorizado")

        # Alert for possibly out-of-coverage zone
        pickup_address = state.get('pickup_address') or ''
        pickup_address_lower = pickup_address.lower() if pickup_address else ''

        if any(zona in pickup_address_lower for zona in ['barranquilla', 'vereda', 'rural', 'fuera']):
            alertas.append("📍 ZONA POSIBLEMENTE FUERA DE COBERTURA - Verifica con política de límites geográficos")

        return alertas

    def _get_default_outbound_greeting_policies(self) -> List[str]:
        """
        Get default policies for OUTBOUND_GREETING phase.

        Always inject these critical policies for the greeting phase.
        """
        all_policies = self.resource_loader.get_all_politicas()

        # Get policies by keywords (fallback if titles change)
        relevant_policies = []

        for title, content in all_policies.items():
            # Always include these policies for outbound greeting
            if any(keyword in title.lower() for keyword in ['grabación', 'identificación', 'verificación', 'calidad']):
                relevant_policies.append(content)

        # If no policies found by keywords, inject top 2 policies
        if not relevant_policies:
            policy_list = list(all_policies.values())
            relevant_policies = policy_list[:2]

        logger.info(f"[CONTEXT_BUILDER] Selected {len(relevant_policies)} default OUTBOUND_GREETING policies")
        return relevant_policies

    def _get_default_outbound_greeting_cases(self) -> List[str]:
        """
        Get default cases for OUTBOUND_GREETING phase.

        Always inject greeting scenarios to help the agent.
        """
        all_cases = self.resource_loader.get_all_casos()

        # Get greeting-related cases
        relevant_cases = []

        for title, content in all_cases.items():
            # Look for greeting/contact-related cases
            if any(keyword in title.lower() for keyword in ['localización', 'contacto', 'identidad', 'confusión']):
                # Limit to first 15 lines to avoid bloat
                case_lines = content.split('\n')[:15]
                relevant_cases.append('\n'.join(case_lines))

        # If no cases found, inject first case
        if not relevant_cases:
            case_list = list(all_cases.values())
            if case_list:
                case_lines = case_list[0].split('\n')[:15]
                relevant_cases = ['\n'.join(case_lines)]

        logger.info(f"[CONTEXT_BUILDER] Selected {len(relevant_cases)} default OUTBOUND_GREETING cases")
        return relevant_cases


# Factory function
def get_context_builder() -> ContextBuilderAgent:
    """Factory function to get ContextBuilderAgent instance"""
    return ContextBuilderAgent()
