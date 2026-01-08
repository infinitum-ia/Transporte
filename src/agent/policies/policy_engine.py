# Policy Engine for evaluating policies
from typing import Dict, Any, List
from src.agent.policies.policy_schema import Policy, PolicyEvaluationResult, PolicyViolation
from src.agent.policies.policy_definitions import ALL_POLICIES

class PolicyEngine:
    def __init__(self, policies: List[Policy] = None):
        self.policies = policies or ALL_POLICIES
    
    def evaluate(self, state: Dict[str, Any], phase: str, direction: str) -> PolicyEvaluationResult:
        applicable = []
        violations = []
        prompt_parts = []
        
        for policy in self.policies:
            if policy.is_applicable(phase, direction):
                applicable.append(policy.id)
                prompt_parts.append(policy.prompt_injection)
                violation = policy.evaluate(state)
                if violation:
                    violations.append(violation)
        
        prompt_injection = '\n\n'.join(prompt_parts) if prompt_parts else ''
        
        return PolicyEvaluationResult(
            applicable_policies=applicable,
            violations=violations,
            prompt_injection=prompt_injection,
            blocking_violations=[],
            has_blocking=False
        )
    
    def get_blocking_violations(self, violations: List[PolicyViolation]) -> List[PolicyViolation]:
        from src.agent.policies.policy_schema import PolicySeverity
        return [v for v in violations if v.severity == PolicySeverity.BLOCKING]
