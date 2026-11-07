"""
End-to-End Autonomous UCIL Orchestration Pipeline.
Integrates all components for complete execution.
"""
from typing import Dict, Any, Tuple
from .cio import CommunicationIntegrityObject
from .dpc import (
    DifferentialPreservationContract, ChangeObligation, NonRegressionObligation,
    BaselineReference, ApprovalRules
)
from .identity_extractors import ContractIdentityExtractor
from .dual_gate import DualGateEvaluator, DualGateVerdict
from .provider_router import ProviderRouter

class UCILPipeline:
    def __init__(self):
        self.extractor = ContractIdentityExtractor()
        self.evaluator = DualGateEvaluator()
        self.router = ProviderRouter()

    def create_dpc(
        self,
        source_text: str,
        amendment_instruction: Dict[str, Any]
    ) -> Tuple[CommunicationIntegrityObject, DifferentialPreservationContract]:
        # 1. Extract CIO
        cio = self.extractor.extract(source_text)

        # 2. Build DPC
        target_name = amendment_instruction.get("target_identity_name", "TIME_PAYMENT_GRACE")
        new_value = amendment_instruction.get("new_value", "60일 이내에 지급")

        change_obligations = []
        non_regression_obligations = []

        for ident in cio.identities:
            if ident.name == target_name:
                change_obligations.append(ChangeObligation(
                    identity_id=ident.identity_id,
                    identity_name=ident.name,
                    baseline_state=ident.canonical_value,
                    required_state=new_value
                ))
            else:
                non_regression_obligations.append(NonRegressionObligation(
                    identity_id=ident.identity_id,
                    identity_name=ident.name,
                    baseline_state=ident.canonical_value,
                    max_allowed_degradation=0.0
                ))

        dpc = DifferentialPreservationContract(
            baseline_ref=BaselineReference(
                document_sha256=cio.source.sha256,
                total_identities=len(cio.identities)
            ),
            change_obligations=change_obligations,
            non_regression_obligations=non_regression_obligations
        )
        return cio, dpc

    def run_pipeline(
        self,
        source_text: str,
        amendment_instruction: Dict[str, Any]
    ) -> Dict[str, Any]:
        cio, dpc = self.create_dpc(source_text, amendment_instruction)

        def eval_wrapper(contract, target):
            return self.evaluator.evaluate(contract, cio, target)

        amended_text, winning_provider, final_verdict = self.router.execute_with_fallback(
            source_text, dpc, eval_wrapper
        )

        return {
            "source_sha256": cio.source.sha256,
            "dpc_id": dpc.dpc_id,
            "identities_extracted": len(cio.identities),
            "change_obligations_count": len(dpc.change_obligations),
            "non_regression_count": len(dpc.non_regression_obligations),
            "winning_provider": winning_provider,
            "routing_history": self.router.history,
            "final_verdict": final_verdict.verdict.value,
            "dual_gate_details": final_verdict.dict(),
            "amended_text": amended_text
        }
