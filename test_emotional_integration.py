"""
Test de verificación de la integración emocional (Opción A).

Este script verifica que:
1. El state tiene los campos emocionales
2. El context_builder puede hacer análisis unificado
3. El prompt_builder inyecta contexto emocional
4. La validación por reglas funciona
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent.graph.state_adapters import create_initial_state
from src.agent.context_builder import ContextBuilderAgent
from src.agent.prompts.prompt_builder import build_prompt
from src.domain.value_objects.conversation_phase import ConversationPhase


def test_state_has_emotional_fields():
    """Test 1: Verificar que el state inicial tiene campos emocionales"""
    print("\n" + "="*80)
    print("TEST 1: State tiene campos emocionales")
    print("="*80)

    state = create_initial_state(
        session_id="test-123",
        call_direction="OUTBOUND",
        agent_name="María"
    )

    # Check emotional fields exist
    assert "emotional_memory" in state, "❌ Falta campo emotional_memory"
    assert "current_sentiment" in state, "❌ Falta campo current_sentiment"
    assert "current_conflict_level" in state, "❌ Falta campo current_conflict_level"
    assert "personality_mode" in state, "❌ Falta campo personality_mode"
    assert "emotional_validation_required" in state, "❌ Falta campo emotional_validation_required"
    assert "validation_attempt_count" in state, "❌ Falta campo validation_attempt_count"

    # Check default values
    assert state["emotional_memory"] == [], "❌ emotional_memory debe iniciar vacía"
    assert state["current_sentiment"] == "Neutro", f"❌ current_sentiment debe ser 'Neutro', no '{state['current_sentiment']}'"
    assert state["current_conflict_level"] == "Bajo", f"❌ current_conflict_level debe ser 'Bajo', no '{state['current_conflict_level']}'"
    assert state["personality_mode"] == "Balanceado", f"❌ personality_mode debe ser 'Balanceado', no '{state['personality_mode']}'"
    assert state["emotional_validation_required"] == False, "❌ emotional_validation_required debe ser False"
    assert state["validation_attempt_count"] == 0, "❌ validation_attempt_count debe ser 0"

    print("✅ PASS: State tiene todos los campos emocionales con valores correctos")
    return True


def test_context_builder_has_unified_analysis():
    """Test 2: Verificar que ContextBuilderAgent tiene el método unificado"""
    print("\n" + "="*80)
    print("TEST 2: ContextBuilderAgent tiene análisis unificado")
    print("="*80)

    try:
        context_builder = ContextBuilderAgent()

        # Check method exists
        assert hasattr(context_builder, '_unified_context_analysis_llm'), \
            "❌ Falta método _unified_context_analysis_llm"

        assert hasattr(context_builder, 'build_context'), \
            "❌ Falta método build_context"

        print("✅ PASS: ContextBuilderAgent tiene el método _unified_context_analysis_llm")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error al inicializar ContextBuilderAgent: {e}")
        return False


def test_prompt_builder_accepts_emotional_analysis():
    """Test 3: Verificar que build_prompt acepta analisis_emocional"""
    print("\n" + "="*80)
    print("TEST 3: prompt_builder acepta analisis_emocional")
    print("="*80)

    try:
        # Test without emotional analysis
        prompt1 = build_prompt(
            phase=ConversationPhase.OUTBOUND_GREETING,
            agent_name="María",
            company_name="Transpormax",
            eps_name="Cosalud",
            known_data={}
        )

        assert len(prompt1) > 0, "❌ Prompt vacío sin análisis emocional"
        print(f"   ✓ Prompt sin análisis emocional: {len(prompt1)} caracteres")

        # Test WITH emotional analysis
        analisis_emocional = {
            "sentiment": "Frustración",
            "conflict_level": "Alto",
            "personality_mode": "Balanceado",
            "emotional_validation_required": True
        }

        prompt2 = build_prompt(
            phase=ConversationPhase.OUTBOUND_SERVICE_CONFIRMATION,
            agent_name="María",
            company_name="Transpormax",
            eps_name="Cosalud",
            known_data={},
            analisis_emocional=analisis_emocional
        )

        assert len(prompt2) > 0, "❌ Prompt vacío con análisis emocional"
        assert len(prompt2) > len(prompt1), "❌ Prompt con análisis debería ser más largo"
        assert "USUARIO FRUSTRADO" in prompt2, "❌ Falta adaptación de frustración en prompt"
        assert "CONFLICTO ALTO" in prompt2, "❌ Falta mención de conflicto alto en prompt"
        assert "VALIDACIÓN EMOCIONAL REQUERIDA" in prompt2, "❌ Falta mención de validación emocional"

        print(f"   ✓ Prompt con análisis emocional: {len(prompt2)} caracteres")
        print(f"   ✓ Contiene adaptación de frustración: ✅")
        print(f"   ✓ Contiene conflicto alto: ✅")
        print(f"   ✓ Contiene validación emocional: ✅")
        print("✅ PASS: prompt_builder correctamente inyecta contexto emocional")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error en build_prompt: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_rules_exist():
    """Test 4: Verificar que existe la función de validación por reglas"""
    print("\n" + "="*80)
    print("TEST 4: Validación por reglas existe")
    print("="*80)

    try:
        from src.agent.graph.nodes.llm_responder import _validate_response_rules

        # Test con respuesta válida
        state = {
            "appointment_date": "2024-01-20",
            "contact_age": "25",
            "next_phase": "OUTBOUND_SERVICE_CONFIRMATION"
        }

        response_valid = "Su cita es el 20 de enero a las 10:00 AM. ¿Confirma?"
        result1 = _validate_response_rules(response_valid, state)

        assert "has_critical_error" in result1, "❌ Falta campo has_critical_error"
        assert "errors" in result1, "❌ Falta campo errors"
        assert "error" in result1, "❌ Falta campo error"

        print(f"   ✓ Validación de respuesta válida:")
        print(f"      - has_critical_error: {result1['has_critical_error']}")
        print(f"      - errors: {result1['errors']}")

        # Test con respuesta problemática (menor de edad)
        state_minor = {
            "appointment_date": "2024-01-20",
            "contact_age": "15",  # MENOR DE EDAD
            "next_phase": "OUTBOUND_SERVICE_CONFIRMATION"
        }

        response_with_data = "Su cita es el 20 de enero con documento CC 12345678 en la dirección Calle 123."
        result2 = _validate_response_rules(response_with_data, state_minor)

        assert result2['has_critical_error'] == True, "❌ Debería detectar revelación a menor"
        assert len(result2['errors']) > 0, "❌ Debería tener errores detectados"

        print(f"   ✓ Validación de respuesta a menor (debería fallar):")
        print(f"      - has_critical_error: {result2['has_critical_error']} ✅")
        print(f"      - errors: {result2['errors']}")

        print("✅ PASS: Validación por reglas funciona correctamente")
        return True

    except ImportError:
        print("❌ FAIL: No se puede importar _validate_response_rules")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error en validación: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "#"*80)
    print("# TEST DE INTEGRACIÓN: Opción A (Integración Ligera)")
    print("#"*80)

    tests = [
        ("State emocional", test_state_has_emotional_fields),
        ("ContextBuilder unificado", test_context_builder_has_unified_analysis),
        ("PromptBuilder emocional", test_prompt_builder_accepts_emotional_analysis),
        ("Validación por reglas", test_validation_rules_exist)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ FAIL: {name} - Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nRESULTADO: {passed}/{total} tests pasaron")

    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! La integración está completa.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests fallaron. Revisar implementación.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
