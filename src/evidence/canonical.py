import json
import dataclasses
from src.evidence.models import EvidenceManifest
from src.evidence.errors import EvidenceCanonicalizationError

def _dataclass_to_dict(obj):
    if dataclasses.is_dataclass(obj):
        result = {}
        for field in dataclasses.fields(obj):
            value = _dataclass_to_dict(getattr(obj, field.name))
            result[field.name] = value
        return result
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_dataclass_to_dict(v) for v in obj]
    else:
        return obj

def canonicalize_evidence(evidence: EvidenceManifest) -> bytes:
    """
    Serializes the EvidenceManifest into a deterministic UTF-8 byte string.
    Uses JSON serialization with sorted keys and compact separators.
    """
    try:
        data = _dataclass_to_dict(evidence)
        canonical_json = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        )
        return canonical_json.encode("utf-8")
    except Exception as e:
        raise EvidenceCanonicalizationError(f"Failed to canonicalize evidence: {e}")
