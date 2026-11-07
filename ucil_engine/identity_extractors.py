"""
Identity Extractors for High-Stakes Legal Contracts.
Implements Claim 1(a), Claim 2, Claim 3.
Extracts SEMANTIC, INTENT, NUMERIC, TEMPORAL, ENTITY, and PRAGMATIC identities.
"""
import re
from typing import List, Dict, Any, Optional
from .cio import (
    CommunicationIdentity, IdentityClass, SourceEvidenceSpan,
    IdentityMetadata, CriticalityEnum, CommunicationIntegrityObject, CommunicationSource
)

class ContractIdentityExtractor:
    """
    Robust hybrid regex + proposition extractor for enterprise contracts.
    """
    def __init__(self, version: str = "3.5.0"):
        self.version = version

    def extract(self, text: str) -> CommunicationIntegrityObject:
        source = CommunicationSource(raw_content=text, language="ko")
        identities: List[CommunicationIdentity] = []

        # 1. Price / Amount (NUMERIC)
        price_patterns = [
            r"금\s*([0-9,]+)\s*원",
            r"([0-9]+)\s*(?:억|천만|백만)\s*원",
            r"([0-9,]+)\s*원"
        ]
        for pat in price_patterns:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.NUMERIC,
                    name="NUM_CONTRACT_PRICE",
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.CRITICAL,
                    metadata=IdentityMetadata(confidence=0.98, extractor_version=self.version)
                ))
                break

        # 2. Payment Deadline / Due Date (TEMPORAL)
        time_patterns = [
            (r"(?:지급기한|인도기한|납품기한)은?\s*([^\r\n.]+?(?:일까지|이내|경과후))", "TIME_DUE_DATE"),
            (r"([0-9]+)\s*일\s*이내에\s*지급", "TIME_PAYMENT_GRACE"),
            (r"([0-9]{1,2}월\s*[0-9]{1,2}일)까지", "TIME_FIXED_DATE")
        ]
        for pat, name in time_patterns:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.TEMPORAL,
                    name=name,
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.HIGH,
                    metadata=IdentityMetadata(confidence=0.95, extractor_version=self.version)
                ))

        # 3. Delay Penalty / Late Fee (NUMERIC)
        penalty_patterns = [
            r"(?:지체상금|연체이자)(?:율은)?\s*([^\r\n.]*?1일당\s*[0-9.]+\s*%)",
            r"(1일당\s*[0-9.]+\s*%)"
        ]
        for pat in penalty_patterns:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.NUMERIC,
                    name="NUM_DELAY_PENALTY",
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.HIGH,
                    metadata=IdentityMetadata(confidence=0.94, extractor_version=self.version)
                ))
                break

        # 4. Indemnification / Liability Cap (SEMANTIC & INTENT)
        indemnity_patterns = [
            (r"손해배상(?:책임)?(?:의\s*범위)?는\s*([^\r\n.]+)", "SEM_LIABILITY_CAP"),
            (r"(고의\s*또는\s*중과실로\s*인한\s*손해는\s*제외한다)", "INT_INDEMNITY_CARVEOUT"),
            (r"(영업비밀\s*침해에\s*대해서는\s*무제한\s*책임을\s*진다)", "INT_CONFIDENTIALITY_UNLIMITED")
        ]
        for pat, name in indemnity_patterns:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.INTENT if "INT" in name else IdentityClass.SEMANTIC,
                    name=name,
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.CRITICAL,
                    metadata=IdentityMetadata(confidence=0.96, extractor_version=self.version)
                ))

        # 5. Termination Clauses (INTENT)
        term_patterns = [
            (r"(서면\s*통지\s*후\s*즉시\s*해지할\s*수\s*있다)", "INT_TERMINATION_IMMEDIATE"),
            (r"(14일의\s*유예기간을\s*두고\s*시정을\s*요구한\s*후\s*해지)", "INT_TERMINATION_CURE_PERIOD"),
            (r"(일방적으로\s*계약을\s*해지할\s*수\s*없다)", "INT_TERMINATION_RESTRICTION")
        ]
        for pat, name in term_patterns:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.INTENT,
                    name=name,
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.HIGH,
                    metadata=IdentityMetadata(confidence=0.92, extractor_version=self.version)
                ))

        # 6. Obligation Modality (PRAGMATIC / POLITENESS)
        modality_patterns = [
            (r"([^\r\n.]+하여야\s*한다)", "PRG_MANDATORY_DUTY"),
            (r"([^\r\n.]+상호\s*협의하여\s*결정한다)", "PRG_DISCRETIONARY_CONSULT")
        ]
        for pat, name in modality_patterns[:3]:
            for match in re.finditer(pat, text):
                span = match.span()
                raw_str = match.group(0).strip()
                identities.append(CommunicationIdentity(
                    identity_class=IdentityClass.PRAGMATIC,
                    name=name,
                    canonical_value=raw_str,
                    source_evidence=SourceEvidenceSpan(
                        span_start=span[0],
                        span_end=span[1],
                        text_snippet=raw_str
                    ),
                    criticality=CriticalityEnum.MEDIUM,
                    metadata=IdentityMetadata(confidence=0.90, extractor_version=self.version)
                ))
                break

        # Deduplicate and return CIO
        unique_identities = []
        seen = set()
        for ident in identities:
            key = (ident.name, str(ident.canonical_value))
            if key not in seen:
                seen.add(key)
                unique_identities.append(ident)

        return CommunicationIntegrityObject(source=source, identities=unique_identities)
