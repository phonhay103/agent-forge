from typing import Protocol, Any, Dict, Optional


class FallbackResolverProtocol(Protocol):
    """
    Protocol for LLM Fallback Repair Mappers.
    Decouples the core variable binder from concrete LLM SDKs or frameworks.
    """
    def repair_payload(
        self,
        context_store: Dict[str, Any],
        target_schema: Dict[str, Any],
        partially_resolved_payload: Any,
        directive: Optional[str] = None
    ) -> Any:
        ...
