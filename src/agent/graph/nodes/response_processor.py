# Response processor node - extract data from LLM response
import logging
from typing import Dict, Any
from src.infrastructure.logging import get_logger

logger = logging.getLogger(__name__)
conv_logger = get_logger().logger


def response_processor(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process LLM response and extract data into state"""

    # Get extracted data from LLM
    extracted = state.get("extracted_data", {})
    prev_phase = state.get("current_phase")

    conv_logger.info(
        "RESPONSE_PROCESSOR",
        extra={
            "event_type": "response_processor",
            "current_phase": state.get("current_phase"),
            "next_phase": state.get("next_phase"),
            "has_extracted": bool(extracted),
            "extracted_keys": list(extracted.keys()) if isinstance(extracted, dict) else [],
        }
    )

    if not extracted:
        # No extraction happened, just update phase
        state["current_phase"] = state.get("next_phase", state.get("current_phase", "GREETING"))
        return state

    # Merge extracted data into state
    # Patient data
    if extracted.get("patient_full_name"):
        state["patient_full_name"] = extracted["patient_full_name"]

    if extracted.get("document_type"):
        state["document_type"] = extracted["document_type"]

    if extracted.get("document_number"):
        state["document_number"] = extracted["document_number"]

    if extracted.get("eps"):
        state["eps"] = extracted["eps"]

    # Contact data (for outbound calls with family/friends)
    if extracted.get("contact_name"):
        state["contact_name"] = extracted["contact_name"]
        logger.info(f"Contact name extracted: {extracted['contact_name']}")
        print(f"✅ Dato extraído: contact_name = '{extracted['contact_name']}'")

    if extracted.get("contact_relationship"):
        state["contact_relationship"] = extracted["contact_relationship"]
        logger.info(f"Contact relationship extracted: {extracted['contact_relationship']}")
        print(f"✅ Dato extraído: contact_relationship = '{extracted['contact_relationship']}'")

    if extracted.get("contact_age"):
        state["contact_age"] = extracted["contact_age"]
        logger.info(f"Contact age extracted: {extracted['contact_age']}")
        print(f"✅ Dato extraído: contact_age = '{extracted['contact_age']}'")

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

    # Special observations (for service modifications)
    if extracted.get("special_observation"):
        state["special_observation"] = extracted["special_observation"]
        logger.info(f"Special observation extracted: {extracted['special_observation']}")

    # Update phase
    state["current_phase"] = state.get("next_phase", state.get("current_phase", "GREETING"))

    # Mark greeting done after first outbound greeting phase
    if prev_phase == "OUTBOUND_GREETING":
        state["greeting_done"] = True

    # NEW: Reset validation counter when phase changes successfully
    if state["current_phase"] != prev_phase:
        state["validation_attempt_count"] = 0

    logger.info(f"Extracted data updated. New phase: {state['current_phase']}")

    return state
