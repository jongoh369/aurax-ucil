"""
Differential Preservation Contract (DPC v1.0)
Implements Claim 1(e), Claim 5, Claim 7, Claim 8, Claim 9 of Patent 10-2026-0165064.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

class PreservationStateEnum(str, Enum):
    PRESERVED = "PRESERVED"
    EQUIVALENT = "EQUIVALENT"
    DEGRADED = "DEGRADED"
    LOST = "LOST"
    TRANSFORMED = "TRANSFORMED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTED = "CONFLICTED"

class ToleranceEnum(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    SEMANTIC_EQUIVALENT = "SEMANTIC_EQUIVALENT"
    NUMERIC_BOUND = "NUMERIC_BOUND"
    SUBSET_PERMITTED = "SUBSET_PERMITTED"

class GateVerdictEnum(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED_CHANGE_FAILURE = "BLOCKED_CHANGE_FAILURE"
    BLOCKED_NON_REGRESSION_FAILURE = "BLOCKED_NON_REGRESSION_FAILURE"
    HOLD_INSUFFICIENT_EVIDENCE = "HOLD_INSUFFICIENT_EVIDENCE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class ChangeObligation(BaseModel):
    obligation_id: str = Field(default_factory=lambda: f"CHG_{uuid.uuid4().hex[:6].upper()}")
    identity_id: str
    identity_name: str
    baseline_state: Any
    required_state: Any
    tolerance: ToleranceEnum = ToleranceEnum.EXACT_MATCH
    min_confidence: float = 0.90
    justification: str = "User specified amendment"

class NonRegressionObligation(BaseModel):
    obligation_id: str = Field(default_factory=lambda: f"NREG_{uuid.uuid4().hex[:6].upper()}")
    identity_id: str
    identity_name: str
    baseline_state: Any
    max_allowed_degradation: float = 0.0
    strict_lock: bool = True
    criticality: str = "HIGH"

class BaselineReference(BaseModel):
    baseline_id: str = Field(default_factory=lambda: f"BASE_{uuid.uuid4().hex[:8].upper()}")
    document_sha256: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_identities: int

class ApprovalRules(BaseModel):
    dual_gate_mode: str = "STRICT_FAIL_CLOSED"
    max_retry_cycles: int = 3
    fallback_action: str = "SWITCH_PROVIDER_THEN_HUMAN"
    require_human_override_on_block: bool = True

class DifferentialPreservationContract(BaseModel):
    schema_version: str = "1.0.0"
    dpc_id: str = Field(default_factory=lambda: f"DPC_{uuid.uuid4().hex[:8].upper()}")
    baseline_ref: BaselineReference
    change_obligations: List[ChangeObligation] = Field(default_factory=list)
    non_regression_obligations: List[NonRegressionObligation] = Field(default_factory=list)
    optional_change_set: List[str] = Field(default_factory=list)
    approval_rules: ApprovalRules = Field(default_factory=ApprovalRules)

    def summary(self) -> Dict[str, Any]:
        return {
            "dpc_id": self.dpc_id,
            "baseline_id": self.baseline_ref.baseline_id,
            "change_count": len(self.change_obligations),
            "non_regression_count": len(self.non_regression_obligations),
            "mode": self.approval_rules.dual_gate_mode
        }
