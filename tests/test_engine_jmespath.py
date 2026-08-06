from src.agent.executor import StaticExecutor as HeadlessExecutor
from src.mcp.schema.models import (
    BlockSummary,
    DivisionSummary,
    OrgStructureOutput,
    ProjectSummary,
    RegionSummary,
    SupplyChainOutput,
)


class DummyClientSession:
    """Mock ClientSession for testing engine variable resolution without MCP network server."""
    pass


def test_engine_jmespath_filter_expression():
    executor = HeadlessExecutor(session=DummyClientSession())
    context_store = {
        "task_1": {
            "products": [
                {"name": "iPhone 15 Pro", "price": 999, "rating": 4.8},
                {"name": "iPhone 15", "price": 799, "rating": 4.6},
                {"name": "MacBook Pro", "price": 1999, "rating": 4.9}
            ]
        }
    }

    # Reference using advanced JMESPath filter expression directly
    val_expr = "$task_1.products[?price > `800` && rating >= `4.8`].name"
    resolved = executor._resolve_variables(val_expr, context_store)

    assert resolved == ["iPhone 15 Pro", "MacBook Pro"]


def test_engine_jmespath_5_level_matrix_flattening():
    executor = HeadlessExecutor(session=DummyClientSession())

    supply_output = SupplyChainOutput(
        network_name="Global Supply",
        total_regions=1,
        total_warehouses=2,
        total_inventory_value=5000.0,
        total_items_count=100,
        low_stock_skus=["SKU-01"],
        region_summaries=[
            RegionSummary(
                region_code="APAC",
                total_blocks=2,
                total_items=100,
                regional_value=5000.0,
                block_summaries=[
                    BlockSummary(block_id="BLK-1", total_quantity=60, total_value=3000.0, manager_name="John"),
                    BlockSummary(block_id="BLK-2", total_quantity=40, total_value=2000.0, manager_name="Alice")
                ]
            )
        ]
    )

    context_store = {"task_1": supply_output}

    # Extract block summaries from nested model using built-in engine JMESPath resolution
    ref1 = "$task_1.region_summaries[*].block_summaries[] | [?total_value > `2500`].block_id"
    resolved1 = executor._resolve_variables(ref1, context_store)
    assert resolved1 == ["BLK-1"]

    ref2 = "$task_1.low_stock_skus[0]"
    resolved2 = executor._resolve_variables(ref2, context_store)
    assert resolved2 == "SKU-01"


def test_engine_jmespath_max_by_function():
    executor = HeadlessExecutor(session=DummyClientSession())

    org_output = OrgStructureOutput(
        company_name="Acme Corp",
        total_divisions=2,
        total_teams=4,
        total_projects=3,
        total_org_budget=800000.0,
        total_work_hours=500.0,
        division_summaries=[
            DivisionSummary(
                division_id="DIV-1",
                division_name="R&D",
                total_teams=2,
                total_budget=500000.0,
                project_summaries=[
                    ProjectSummary(project_id="P1", project_name="AI Alpha", budget=500000.0, total_tasks=10, total_hours=200.0)
                ]
            ),
            DivisionSummary(
                division_id="DIV-2",
                division_name="Marketing",
                total_teams=2,
                total_budget=300000.0,
                project_summaries=[
                    ProjectSummary(project_id="P2", project_name="Global Launch", budget=300000.0, total_tasks=5, total_hours=100.0)
                ]
            )
        ]
    )

    context_store = {"task_1": org_output}

    # Built-in JMESPath resolution using max_by function without requiring a tool
    ref = "$task_1.division_summaries | max_by(@, &total_budget).division_name"
    resolved = executor._resolve_variables(ref, context_store)
    assert resolved == "R&D"


def test_engine_nested_dict_argument_resolution():
    executor = HeadlessExecutor(session=DummyClientSession())
    context_store = {
        "task_1": {
            "tags": ["python", "ai", "mcp"],
            "scores": [88, 92, 95]
        }
    }

    tool_args = {
        "tag_string": "$task_1.tags | join(', ', @)",
        "max_score": "$task_1.scores | max_by(@, &@)",
        "static_param": "hello"
    }

    resolved_args = executor._resolve_variables(tool_args, context_store)

    assert resolved_args == {
        "tag_string": "python, ai, mcp",
        "max_score": 95,
        "static_param": "hello"
    }


if __name__ == "__main__":
    test_engine_jmespath_filter_expression()
    test_engine_jmespath_5_level_matrix_flattening()
    test_engine_jmespath_max_by_function()
    test_engine_nested_dict_argument_resolution()
    print("All engine built-in JMESPath resolution tests passed successfully!")
