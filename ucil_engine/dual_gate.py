"""
Dual Gate Evaluation Engine & Traceability Graph.
Implements Claim 1(g), 1(h), Claim 5, Claim 6, Claim 11.
"""
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
import hashlib
from .cio import CommunicationIntegrityObject, CommunicationIdentity
from .dpc import (
    DifferentialPreservationContract, GateVerdictEnum,
    PreservationStateEnum, ChangeObligation, NonRegressionObligation, ToleranceEnum
)

class EvaluationDetail(BaseModel):
    obligation_id: str
    identity_name: str
    target_text_found: Optional[str] = None
    preservation_state: PreservationStateEnum
    passed: bool
    evidence_snippet: str
    reason: str

class GateResult(BaseModel):
    gate_name: str
    passed: bool
    details: List[EvaluationDetail]
    failure_reasons: List[str] = Field(default_factory=list)

class DualGateVerdict(BaseModel):
    verdict: GateVerdictEnum
    gate1_change_result: GateResult
    gate2_non_regression_result: GateResult
    reasons: List[str]
    audit_hash: str
    execution_time_ms: float = 0.0

class DualGateEvaluator:
    """
    Evaluates modified document against DPC specifications.
    Fail-Closed rule: Both Gate 1 and Gate 2 must PASS for APPROVED verdict.
    """
    def __init__(self, tolerance_strictness: float = 0.95):
        self.tolerance_strictness = tolerance_strictness

    def evaluate(
        self,
        dpc: DifferentialPreservationContract,
        source_cio: CommunicationIntegrityObject,
        target_text: str
    ) -> DualGateVerdict:
        target_clean = " ".join(target_text.split())

        # ---------------- Gate 1: Change Obligation Evaluation ----------------
        g1_details: List[EvaluationDetail] = []
        g1_failures: List[str] = []

        for chg in dpc.change_obligations:
            req_str = str(chg.required_state).strip()
            # Check presence of required state in target
            if req_str in target_text or req_str in target_clean:
                detail = EvaluationDetail(
                    obligation_id=chg.obligation_id,
                    identity_name=chg.identity_name,
                    target_text_found=req_str,
                    preservation_state=PreservationStateEnum.PRESERVED,
                    passed=True,
                    evidence_snippet=req_str,
                    reason="Required change state successfully reflected in target text."
                )
            else:
                detail = EvaluationDetail(
                    obligation_id=chg.obligation_id,
                    identity_name=chg.identity_name,
                    target_text_found=None,
                    preservation_state=PreservationStateEnum.DEGRADED,
                    passed=False,
                    evidence_snippet="",
                    reason=f"Required change '{req_str}' not found in target text."
                )
                g1_failures.append(f"Change Obligation Failed: [{chg.identity_name}] not matched.")
            g1_details.append(detail)

        gate1_passed = len(g1_failures) == 0
        gate1_result = GateResult(gate_name="Gate 1 (Change Obligations)", passed=gate1_passed, details=g1_details, failure_reasons=g1_failures)

        # ---------------- Gate 2: Non-Regression Obligation Evaluation ----------------
        g2_details: List[EvaluationDetail] = []
        g2_failures: List[str] = []

        for nreg in dpc.non_regression_obligations:
            base_str = str(nreg.baseline_state).strip()

            # Strict preservation check
            if base_str in target_text or base_str in target_clean:
                detail = EvaluationDetail(
                    obligation_id=nreg.obligation_id,
                    identity_name=nreg.identity_name,
                    target_text_found=base_str,
                    preservation_state=PreservationStateEnum.PRESERVED,
                    passed=True,
                    evidence_snippet=base_str,
                    reason="Baseline obligation preserved without regression."
                )
            else:
                # Regressed! Check if it was transformed or lost
                detail = EvaluationDetail(
                    obligation_id=nreg.obligation_id,
                    identity_name=nreg.identity_name,
                    target_text_found=None,
                    preservation_state=PreservationStateEnum.LOST,
                    passed=False,
                    evidence_snippet="",
                    reason=f"CRITICAL REGRESSION: Baseline obligation '{base_str}' was modified or omitted."
                )
                g2_failures.append(f"Non-Regression Obligation Violated: [{nreg.identity_name}] baseline lost.")
            g2_details.append(detail)

        gate2_passed = len(g2_failures) == 0
        gate2_result = GateResult(gate_name="Gate 2 (Non-Regression Obligations)", passed=gate2_passed, details=g2_details, failure_reasons=g2_failures)

        # ---------------- Final Dual-Gate Synthesis ----------------
        reasons = []
        if gate1_passed and gate2_passed:
            verdict = GateVerdictEnum.APPROVED
            reasons.append("All change obligations fulfilled AND all non-regression baselines strictly preserved.")
        elif not gate1_passed and gate2_passed:
            verdict = GateVerdictEnum.BLOCKED_CHANGE_FAILURE
            reasons.extend(g1_failures)
        elif gate1_passed and not gate2_passed:
            verdict = GateVerdictEnum.BLOCKED_NON_REGRESSION_FAILURE
            reasons.extend(g2_failures)
        else:
            verdict = GateVerdictEnum.BLOCKED_NON_REGRESSION_FAILURE
            reasons.extend(g1_failures)
            reasons.extend(g2_failures)

        # Cryptographic Audit Hash for Verdict
        hasher = hashlib.sha256()
        hasher.update(dpc.dpc_id.encode('utf-8'))
        hasher.update(verdict.value.encode('utf-8'))
        for r in reasons:
            hasher.update(r.encode('utf-8'))
        audit_hash = hasher.hexdigest()

        return DualGateVerdict(
            verdict=verdict,
            gate1_change_result=gate1_result,
            gate2_non_regression_result=gate2_result,
            reasons=reasons,
            audit_hash=audit_hash
        )
