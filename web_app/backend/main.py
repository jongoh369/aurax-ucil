"""
AuraX-UCIL Enterprise Platform - FastAPI Backend
Provides full REST API for contract upload, CIO extraction, DPC compilation,
autonomous provider switching, Dual-Gate verification, and cryptographic audit.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import sys
import hashlib
import time

# Add core engine to path
ENGINE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../03_Core_Engine_Source"))
if ENGINE_PATH not in sys.path:
    sys.path.insert(0, ENGINE_PATH)

from ucil_engine.pipeline import UCILPipeline
from ucil_engine.cio import CommunicationIntegrityObject
from ucil_engine.dpc import DifferentialPreservationContract, GateVerdictEnum

app = FastAPI(
    title="AuraX-UCIL Enterprise AI Integrity API",
    description="Patent 10-2026-0165064: Differential Preservation Contract & Non-Regression Gateway",
    version="3.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = UCILPipeline()

# In-memory session store
CONTRACT_STORE: Dict[str, Dict[str, Any]] = {}
AUDIT_STORE: Dict[str, Dict[str, Any]] = {}

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    sha256: str
    char_count: int
    preview: str

class AmendmentRequest(BaseModel):
    document_id: str
    target_identity_name: str = "TIME_PAYMENT_GRACE"
    new_value: str = "60일 이내에 지급"
    instructions: Optional[str] = "Extend payment grace period while preserving all liabilities and penalties."

class PipelineExecutionResponse(BaseModel):
    execution_id: str
    dpc_id: str
    winning_provider: str
    routing_attempts: List[Dict[str, Any]]
    final_verdict: str
    change_fulfilled: bool
    non_regression_held: bool
    amended_contract_text: str
    audit_hash: str
    execution_time_ms: float

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "HEALTHY",
        "engine_version": "3.5.0",
        "patent": "10-2026-0165064",
        "timestamp": time.time()
    }

@app.post("/api/v1/contracts/upload", response_model=UploadResponse)
async def upload_contract(
    file: Optional[UploadFile] = None,
    raw_text: Optional[str] = Form(None)
):
    """
    Upload contract document (DOCX, PDF, or Plain Text).
    """
    content = ""
    filename = "raw_input.txt"
    if file:
        filename = file.filename
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8", errors="ignore")
    elif raw_text:
        content = raw_text
    else:
        # Default sample contract if empty
        content = """제1조 (대금 지급) 을은 개발 완료 후 검수를 거쳐 30일 이내에 지급한다. 계약 총액은 금 50,000,000원으로 한다.
제2조 (지체상금) 을이 지급을 지체할 경우 지체상금율은 1일당 0.1%로 한다.
제3조 (손해배상) 손해배상책임의 범위는 계약금액을 한도로 하되, 고의 또는 중과실로 인한 손해는 제외한다.
제4조 (계약 해지) 일방 당사자가 계약을 위반할 경우 14일의 유예기간을 두고 시정을 요구한 후 해지할 수 있다."""
        filename = "standard_service_contract.txt"

    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    doc_id = f"DOC_{sha256[:10].upper()}"

    CONTRACT_STORE[doc_id] = {
        "document_id": doc_id,
        "filename": filename,
        "content": content,
        "sha256": sha256
    }

    return UploadResponse(
        document_id=doc_id,
        filename=filename,
        sha256=sha256,
        char_count=len(content),
        preview=content[:200] + "..."
    )

@app.post("/api/v1/contracts/cio/extract")
def extract_cio(document_id: str):
    """
    Extracts Communication Integrity Object (CIO v1.0) with multi-identities.
    """
    if document_id not in CONTRACT_STORE:
        raise HTTPException(status_code=404, detail="Document not found")
    
    text = CONTRACT_STORE[document_id]["content"]
    cio = pipeline.extractor.extract(text)
    return {
        "document_id": document_id,
        "cio": cio.dict()
    }

@app.post("/api/v1/dpc/compile")
def compile_dpc(req: AmendmentRequest):
    """
    Compiles Differential Preservation Contract (DPC v1.0) from amendment instruction.
    """
    if req.document_id not in CONTRACT_STORE:
        raise HTTPException(status_code=404, detail="Document not found")

    text = CONTRACT_STORE[req.document_id]["content"]
    cio, dpc = pipeline.create_dpc(text, {
        "target_identity_name": req.target_identity_name,
        "new_value": req.new_value
    })
    return {
        "dpc": dpc.dict(),
        "summary": dpc.summary()
    }

@app.post("/api/v1/dpc/execute", response_model=PipelineExecutionResponse)
def execute_amendment_pipeline(req: AmendmentRequest):
    """
    Executes full autonomous pipeline: DPC creation -> Provider Routing -> Dual Gate.
    """
    if req.document_id not in CONTRACT_STORE:
        raise HTTPException(status_code=404, detail="Document not found")

    t_start = time.time()
    source_text = CONTRACT_STORE[req.document_id]["content"]
    
    result = pipeline.run_pipeline(source_text, {
        "target_identity_name": req.target_identity_name,
        "new_value": req.new_value
    })
    elapsed_ms = (time.time() - t_start) * 1000.0

    exec_id = f"EXEC_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()}"
    gate_details = result["dual_gate_details"]

    response = PipelineExecutionResponse(
        execution_id=exec_id,
        dpc_id=result["dpc_id"],
        winning_provider=result["winning_provider"],
        routing_attempts=result["routing_history"],
        final_verdict=result["final_verdict"],
        change_fulfilled=gate_details["gate1_change_result"]["passed"],
        non_regression_held=gate_details["gate2_non_regression_result"]["passed"],
        amended_contract_text=result["amended_text"],
        audit_hash=gate_details["audit_hash"],
        execution_time_ms=round(elapsed_ms, 2)
    )

    AUDIT_STORE[exec_id] = response.dict()
    return response

@app.get("/api/v1/audit/{execution_id}/report")
def get_audit_certificate(execution_id: str):
    """
    Retrieves verifiable cryptographic audit certificate.
    """
    if execution_id not in AUDIT_STORE:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return AUDIT_STORE[execution_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
