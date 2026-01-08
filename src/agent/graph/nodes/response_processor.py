# Response processor node - extract data from LLM response
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def response_processor(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process LLM response and extract data into state"""

    # Get extracted data from LLM
    extracted = state.get("extracted_data", {})

    if not extracted:
        # No extraction happened, just update phase
        state["current_phase"] = state.get("next_phase", state.get("current_phase", "GREETING"))
        return state

    # Merge extracted data into state
    # Patient data
    if extracted.get("patient_full_name"):
        state["patient_full_name"] = extracted["patient_full_name"]

    if extracted.get("document_type"):
        state["patient_document_type"] = extracted["document_type"]

    if extracted.get("document_number"):
        state["patient_document_number"] = extracted["document_number"]

    if extracted.get("eps"):
        state["patient_eps"] = extracted["eps"]

    # Service data
    if extracted.get("service_type"):
        state["service_type"] = extracted["service_type"]

    if extracted.get("appointment_date"):
        state["appointment_date"] = extracted["appointment_date"]

    if extracted.get("appointment_time"):
        state["appointment_time"] = extracted["appointment_time"]

    if extracted.get("pickup_address"):
        state["pickup_address"] = extracted["pickup_address"]

    # Incidents
    if extracted.get("incident_summary"):
        incidents = state.get("incidents", [])
        incidents.append({
            "summary": extracted["incident_summary"],
            "timestamp": state.get("_current_timestamp", "")
        })
        state["incidents"] = incidents

    # Update phase
    state["current_phase"] = state.get("next_phase", state.get("current_phase", "GREETING"))

    logger.info(f"Extracted data updated. New phase: {state['current_phase']}")

    return state
