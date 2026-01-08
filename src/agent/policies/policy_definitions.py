# Policy definitions file
from typing import Dict, Any, Optional, List
from src.agent.policies.policy_schema import Policy, PolicyCategory, PolicySeverity, PolicyViolation

def check_conductor_assignment_request(state: Dict[str, Any]) -> Optional[PolicyViolation]:
    messages = state.get('messages', [])
    if not messages:
        return None
    last_msg = ''
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_msg = msg.content.lower()
            break
    keywords = ['quiero al conductor', 'prefiero al conductor']
    for kw in keywords:
        if kw in last_msg:
            return PolicyViolation('CONDUCTOR_001', 'Limite Conductores', PolicySeverity.WARNING, 'Solicita conductor', 'msg', last_msg[:50], 'Enviar sugerencia', 'Enviare sugerencia')
    return None

def check_eps_authorization(state: Dict[str, Any]) -> Optional[PolicyViolation]:
    eps = (state.get('eps') or '').lower()
    if eps and eps != 'cosalud':
        return PolicyViolation('SERVICIO_001', 'Solo Cosalud', PolicySeverity.BLOCKING, 'EPS incorrecta', 'eps', eps, 'Contactar EPS', 'Solo Cosalud')
    return None

def check_geographic_coverage(state: Dict[str, Any]) -> Optional[PolicyViolation]:
    addr = (state.get('pickup_address') or '').lower()
    if any(k in addr for k in ['vereda', 'rural', ' km ']):
        return PolicyViolation('GEOGRAFIA_001', 'Cobertura', PolicySeverity.BLOCKING, 'Fuera cobertura', 'address', addr[:50], 'EPS', 'Solo urbano')
    return None

def check_transport_modality_request(state: Dict[str, Any]) -> Optional[PolicyViolation]:
    messages = state.get('messages', [])
    if not messages:
        return None
    last_msg = ''
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_msg = msg.content.lower()
            break
    if any(k in last_msg for k in ['expreso', 'exclusivo']):
        return PolicyViolation('MODALIDAD_001', 'Ruta vs Expreso', PolicySeverity.WARNING, 'Solicita expreso', 'msg', last_msg[:50], 'EPS', 'Estandar ruta')
    return None

def check_recording_notice_given(state: Dict[str, Any]) -> Optional[PolicyViolation]:
    return None

CONDUCTOR_001 = Policy('CONDUCTOR_001', 'Limite Conductores', PolicyCategory.CONDUCTOR, 'No asignar', PolicySeverity.WARNING, ['*'], ['BOTH'], check_conductor_assignment_request, 'Enviare sugerencia', 'No asignes conductores', ['conductor'])
SERVICIO_001 = Policy('SERVICIO_001', 'Solo Cosalud', PolicyCategory.SERVICIO, 'Solo Cosalud', PolicySeverity.BLOCKING, ['IDENTIFICATION'], ['BOTH'], check_eps_authorization, 'Solo Cosalud', 'CRITICO: Solo Cosalud', ['eps'])
GEOGRAFIA_001 = Policy('GEOGRAFIA_001', 'Cobertura SM', PolicyCategory.GEOGRAFIA, 'Solo urbano', PolicySeverity.BLOCKING, ['SERVICE_COORDINATION'], ['BOTH'], check_geographic_coverage, 'Solo urbano', 'CRITICO: Solo urbano', ['vereda'])
MODALIDAD_001 = Policy('MODALIDAD_001', 'Ruta', PolicyCategory.MODALIDAD, 'Ruta std', PolicySeverity.WARNING, ['SERVICE_COORDINATION'], ['BOTH'], check_transport_modality_request, 'Ruta std', 'Ruta std', ['expreso'])
PROTOCOLO_001 = Policy('PROTOCOLO_001', 'Grabacion', PolicyCategory.PROTOCOLO, 'Informar', PolicySeverity.BLOCKING, ['GREETING'], ['BOTH'], check_recording_notice_given, 'Grabada', 'Informa grabacion', ['grab'])

ALL_POLICIES = [CONDUCTOR_001, SERVICIO_001, GEOGRAFIA_001, MODALIDAD_001, PROTOCOLO_001]

def get_policy_by_id(pid: str) -> Optional[Policy]:
    return next((p for p in ALL_POLICIES if p.id == pid), None)

def get_policies_by_category(cat: PolicyCategory) -> List[Policy]:
    return [p for p in ALL_POLICIES if p.category == cat]

def get_policies_by_severity(sev: PolicySeverity) -> List[Policy]:
    return [p for p in ALL_POLICIES if p.severity == sev]
