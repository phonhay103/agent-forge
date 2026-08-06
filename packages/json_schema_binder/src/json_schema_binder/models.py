from collections.abc import Mapping
from typing import Any, Generic, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field

PrimitiveType = Union[str, int, float, bool, bytes, None]
ComplexType = Union[dict[str, Any], list[Any], BaseModel]
SupportedDataType = Union[PrimitiveType, ComplexType]

T = TypeVar("T")


class BindingContext(BaseModel):
    """
    Structured container for source data context.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: dict[str, SupportedDataType] = Field(
        default_factory=dict,
        description="Source data namespaces or root objects."
    )
    metadata: dict[str, SupportedDataType] = Field(
        default_factory=dict,
        description="Optional metadata or schema store."
    )

    @classmethod
    def from_dict(cls, raw_context: Union["BindingContext", Mapping[str, Any]]) -> "BindingContext":
        if isinstance(raw_context, BindingContext):
            return raw_context

        formatted_data = {}
        for k, v in raw_context.items():
            if hasattr(v, "model_dump"):
                formatted_data[k] = v.model_dump()
            elif hasattr(v, "__dataclass_fields__"):
                from dataclasses import asdict
                formatted_data[k] = asdict(v)
            else:
                formatted_data[k] = v
        return cls(data=formatted_data)


class MappingSpec(BaseModel):
    """
    Direct mapping specification binding target field names to expression strings.
    """
    field_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Map of target_field -> expression_string (e.g. {'amount': 'inventory.total_value'})"
    )


class EvaluationResult(BaseModel, Generic[T]):
    """
    Result contract from evaluating a single expression.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: T = Field(description="The evaluated output value.")
    expression: str = Field(description="The evaluated expression string.")
    is_success: bool = Field(description="True if evaluation succeeded.")
    engine: str = Field(description="Binding engine used.")
    error: str | None = Field(default=None, description="Error message if evaluation failed.")


class MappingResult(BaseModel, Generic[T]):
    """
    Result contract from schema/payload transformation.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    output: T = Field(description="The mapped and schema-validated output.")
    is_success: bool = Field(description="True if mapping succeeded.")
    engine: str = Field(description="Binding engine used.")
    unresolved_expressions: list[str] = Field(
        default_factory=list,
        description="List of expressions that failed to evaluate or match."
    )
    errors: list[str] = Field(default_factory=list, description="Any evaluation or validation errors.")
