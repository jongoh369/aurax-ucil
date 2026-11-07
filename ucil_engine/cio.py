"""
Communication Integrity Object (CIO v1.0)
Implements Claim 1(a), Claim 2, Claim 3, Claim 4 of Patent 10-2026-0165064.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import hashlib
import uuid

class IdentityClass(str, Enum):
    SEMANTIC = "SEMANTIC"
    INTENT = "INTENT"
    PRAGMATIC = "PRAGMATIC"
    POLITENESS = "POLITENESS"
    ENTITY = "ENTITY"
    NUMERIC = "NUMERIC"
    TEMPORAL = "TEMPORAL"
    PRONUNCIATION = "PRONUNCIATION"

class ModalityEnum(str, Enum):
    TEXT = "TEXT"
    SPEECH = "SPEECH"
    MULTIMODAL = "MULTIMODAL"

class CriticalityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SourceEvidenceSpan(BaseModel):
    span_start: int = Field(..., description="Character offset start")
    span_end: int = Field(..., description="Character offset end")
    text_snippet: str = Field(..., description="Exact literal text slice")
    token_count: Optional[int] = None

class IdentityMetadata(BaseModel):
    extractor_version: str = "3.5.0"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    relation_type: str = "DIRECT_EXTRACTED"
    created_at: Optional[str] = None

class CommunicationIdentity(BaseModel):
    identity_id: str = Field(default_factory=lambda: f"ID_{uuid.uuid4().hex[:8].upper()}")
    identity_class: IdentityClass
    name: str = Field(..., description="Human readable label, e.g. NUM_PRICE, TIME_DUE")
    canonical_value: Union[str, Dict[str, Any], int, float, List[Any]]
    source_evidence: SourceEvidenceSpan
    criticality: CriticalityEnum = CriticalityEnum.HIGH
    metadata: IdentityMetadata = Field(default_factory=IdentityMetadata)

class CommunicationSource(BaseModel):
    modality: ModalityEnum = ModalityEnum.TEXT
    language: str = "ko"
    raw_content: str
    sha256: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.sha256 and self.raw_content:
            self.sha256 = hashlib.sha256(self.raw_content.encode('utf-8')).hexdigest()

class CommunicationIntegrityObject(BaseModel):
    schema_version: str = "1.0.0"
    communication_id: str = Field(default_factory=lambda: f"COMM_{uuid.uuid4().hex[:12].upper()}")
    source: CommunicationSource
    identities: List[CommunicationIdentity] = Field(default_factory=list)

    def get_identity(self, identity_id: str) -> Optional[CommunicationIdentity]:
        for ident in self.identities:
            if ident.identity_id == identity_id:
                return ident
        return None

    def filter_by_class(self, id_class: IdentityClass) -> List[CommunicationIdentity]:
        return [i for i in self.identities if i.identity_class == id_class]
