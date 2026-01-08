"""
Policy schema definitions for the conversation agent.

This module defines the data structures for the policy-based validation system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Dict, Any


class PolicyCategory(str, Enum):
    """Categories of policies"""
    CONDUCTOR = "CONDUCTOR"
    SERVICIO = "SERVICIO"
    GEOGRAFIA = "GEOGRAFIA"
    MODALIDAD = "MODALIDAD"
    PROTOCOLO = "PROTOCOLO"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations"""
    INFO = "INFO"           # Informational, no action required
    WARNING = "WARNING"     # Warning, agent can continue but should note
    BLOCKING = "BLOCKING"   # Blocking, agent must escalate or stop


@dataclass
class PolicyViolation:
    """Represents a detected policy violation"""
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    description: str
    detected_in_field: Optional[str] = None
    detected_value: Optional[str] = None
    recommended_action: Optional[str] = None
    response_template: Optional[str] = None


@dataclass
class PolicyEvaluationResult:
    """Result of evaluating policies against current state"""
    applicable_policies: List[str]
    violations: List[PolicyViolation]
    prompt_injection: str
    blocking_violations: List[PolicyViolation]
    has_blocking: bool
    
    def __post_init__(self):
        self.blocking_violations = [v for v in self.violations if v.severity == PolicySeverity.BLOCKING]
        self.has_blocking = len(self.blocking_violations) > 0


@dataclass
class Policy:
    """
    Definition of a policy that can be evaluated against conversation state.
    
    Policies encapsulate business rules and constraints that must be enforced
    before or during LLM invocation.
    """
    id: str
    """Unique policy identifier (e.g., CONDUCTOR_001)"""
    
    name: str
    """Human-readable policy name"""
    
    category: PolicyCategory
    """Policy category for organization"""
    
    description: str
    """Detailed description of the policy"""
    
    severity: PolicySeverity
    """Severity level if policy is violated"""
    
    applicable_phases: List[str]
    """List of phases where this policy applies (* = all phases)"""
    
    applicable_directions: List[str]
    """List of call directions where this applies (INBOUND, OUTBOUND, BOTH)"""
    
    check_function: Callable[[Dict[str, Any]], Optional[PolicyViolation]]
    """Function that checks if policy is violated. Returns PolicyViolation if violated, None otherwise."""
    
    response_template: str = ""
    """Template response for when policy is violated"""
    
    prompt_injection: str = ""
    """Text to inject into prompt when this policy is applicable"""
    
    keywords: List[str] = field(default_factory=list)
    """Keywords that trigger this policy check"""
    
    def is_applicable(self, phase: str, direction: str) -> bool:
        """
        Check if this policy is applicable for the given phase and direction.
        
        Args:
            phase: Current conversation phase
            direction: Call direction (INBOUND or OUTBOUND)
            
        Returns:
            True if policy is applicable, False otherwise
        """
        # Check phase
        if '*' not in self.applicable_phases and phase not in self.applicable_phases:
            return False
        
        # Check direction
        if 'BOTH' in self.applicable_directions:
            return True
        
        return direction in self.applicable_directions
    
    def evaluate(self, state: Dict[str, Any]) -> Optional[PolicyViolation]:
        """
        Evaluate this policy against the current state.
        
        Args:
            state: Current conversation state
            
        Returns:
            PolicyViolation if policy is violated, None otherwise
        """
        return self.check_function(state)
