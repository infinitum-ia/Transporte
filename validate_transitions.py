"""
Script de validación de transiciones de fase

Verifica que las transiciones definidas en prompts coincidan con el dominio.
"""
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.agent.prompts.langgraph_prompts import get_valid_next_phases


def validate_transitions():
    """Valida que las transiciones en prompts coincidan con el dominio"""

    print("=" * 80)
    print("VALIDACIÓN DE TRANSICIONES DE FASE")
    print("=" * 80)
    print()

    errors = []
    warnings = []

    # Obtener todas las fases outbound
    outbound_phases = [
        ConversationPhase.OUTBOUND_GREETING,
        ConversationPhase.OUTBOUND_LEGAL_NOTICE,
        ConversationPhase.OUTBOUND_SERVICE_CONFIRMATION,
        ConversationPhase.OUTBOUND_SPECIAL_CASES,
        ConversationPhase.OUTBOUND_CLOSING,
    ]

    for phase in outbound_phases:
        print(f"\n📋 Validando: {phase.value}")
        print("-" * 80)

        # Obtener transiciones del dominio
        domain_transitions = [str(p) for p in phase.get_next_phases()]

        # Obtener transiciones de los prompts
        prompt_transitions_str = get_valid_next_phases(phase)
        prompt_transitions = [t.strip('"') for t in prompt_transitions_str.split(" | ")]

        print(f"  Dominio:  {domain_transitions}")
        print(f"  Prompts:  {prompt_transitions}")

        # Validar que cada transición del prompt esté en el dominio
        # Permitir que el prompt tenga un subset o mismas transiciones
        for pt in prompt_transitions:
            if pt not in domain_transitions and pt != phase.value:
                # Permitir loops (phase → phase)
                if pt == phase.value:
                    warnings.append(f"{phase.value} → {pt} (loop permitido)")
                else:
                    errors.append(f"{phase.value} → {pt} NO está en dominio")

        # Validar que todas las transiciones del dominio estén en los prompts
        # (excepto loops, que son opcionales en prompts)
        for dt in domain_transitions:
            if dt not in prompt_transitions and dt != phase.value:
                errors.append(f"{phase.value} → {dt} falta en prompts")

        # Validar loops correctamente
        if phase.value in prompt_transitions:
            if phase.value not in domain_transitions:
                # El prompt permite loop pero el dominio no
                # Verificar si el dominio permite can_transition_to self
                if phase.can_transition_to(phase):
                    print(f"  ✅ Loop permitido: {phase.value} → {phase.value}")
                else:
                    errors.append(f"{phase.value} → {phase.value} (loop) NO permitido en dominio")

        if not errors and not warnings:
            print(f"  ✅ Transiciones válidas")

    print("\n" + "=" * 80)
    print("RESULTADO")
    print("=" * 80)

    if errors:
        print(f"\n❌ ERRORES ENCONTRADOS ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")

    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")

    if not errors and not warnings:
        print("\n✅ TODAS LAS TRANSICIONES SON VÁLIDAS")

    print("\n" + "=" * 80)
    print("RESUMEN DE TRANSICIONES OUTBOUND")
    print("=" * 80)

    print("""
    OUTBOUND_GREETING
        → OUTBOUND_GREETING (loop, espera/transferencia)
        → OUTBOUND_LEGAL_NOTICE (identificación completa)
        → END (número equivocado, menor edad sin adulto)

    OUTBOUND_LEGAL_NOTICE
        → OUTBOUND_SERVICE_CONFIRMATION (normal)
        → OUTBOUND_SPECIAL_CASES (queja temprana)

    OUTBOUND_SERVICE_CONFIRMATION
        → OUTBOUND_SERVICE_CONFIRMATION (loop, solicitud especial)
        → OUTBOUND_SPECIAL_CASES (queja, cambio, problema)
        → OUTBOUND_CLOSING (confirmación exitosa)

    OUTBOUND_SPECIAL_CASES
        → OUTBOUND_SERVICE_CONFIRMATION (loop para confirmar cambios)
        → OUTBOUND_CLOSING (caso resuelto)

    OUTBOUND_CLOSING
        → OUTBOUND_CLOSING (loop, preguntas adicionales)
        → END (despedida final)
    """)

    return len(errors) == 0


if __name__ == "__main__":
    success = validate_transitions()
    exit(0 if success else 1)
