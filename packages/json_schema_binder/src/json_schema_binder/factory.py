from json_schema_binder.base import _BINDING_ENGINES_REGISTRY, BaseBindingEngine, BindingType

# Import concrete engines to ensure decorator registration triggers at startup


def get_binding_engine(binding_type: str | BindingType = BindingType.JMESPATH) -> BaseBindingEngine:
    """
    Factory function to retrieve an independent binding engine instance using dynamic registry.
    """
    if isinstance(binding_type, BindingType):
        binding_type_str = binding_type.value
    else:
        binding_type_str = str(binding_type).lower().strip()

    engine_class = _BINDING_ENGINES_REGISTRY.get(binding_type_str)
    if engine_class is not None:
        return engine_class()

    supported_engines = sorted(_BINDING_ENGINES_REGISTRY.keys())
    raise ValueError(
        f"Unsupported binding_type: '{binding_type}'. Supported registered binding types are: {supported_engines}"
    )
