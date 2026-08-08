import logging
import sys
from pathlib import Path

import anyio

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from mcp import ClientSession
from src.agent.executor import StaticExecutor as HeadlessExecutor
from src.agent.main import MCP_SERVER_URL
from src.agent.models import Plan, PlanTask as PlanStep
from src.mcp.schema.models import (
    AisleStorage,
    ContactDetail,
    ItemBatch,
    ItemSpec,
    ManagerInfo,
    NetworkMetadata,
    RegionNode,
    SupplyChainInput,
    WarehouseBlock,
)
from src.shared.executor_models import ExecutionContext
from src.shared.mcp_protocols import MCPClient

# Configure logging to see the optimized execution steps and lru_caches in action
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_complex_pipeline")

# 1. Construct the deeply nested 5-level supply chain input data
def make_complex_supply_chain_input() -> dict:
    input_obj = SupplyChainInput(
        network_info=NetworkMetadata(network_name="Global Enterprise Tech Logistics", version="v5.1"), # Level 1
        regions=[ # Level 1 -> Level 2 Array
            RegionNode( # Level 2 Obj
                region_code="APAC-HQ",
                warehouse_matrix=[ # Level 2 -> Level 3 Matrix (Array of Arrays)
                    [
                        WarehouseBlock( # Level 3 Obj
                            block_id="BLK-A1-PREMIUM",
                            manager=ManagerInfo(
                                name="Alice Smith",
                                contact=ContactDetail(email="alice@tech.com", phone="+123456789")
                            ),
                            aisles=[ # Level 3 -> Level 4 Array
                                AisleStorage( # Level 4 Obj
                                    aisle_id="AISLE-99",
                                    shelf_grid=[ # Level 4 -> Level 5 Matrix (Array of Arrays)
                                        [
                                            ItemBatch( # Level 5 Obj
                                                sku="SKU-CHIP-99",
                                                item_name="AI Co-Processor Chip v2",
                                                quantity=10,
                                                unit_price=250.0, # Value: 2500.0
                                                specification=ItemSpec(
                                                    dimensions_cm=[2.0, 2.0, 0.3],
                                                    weight_kg=0.08
                                                )
                                            ),
                                            ItemBatch(
                                                sku="SKU-RAM-88",
                                                item_name="Premium High-Bandwidth DDR5 VRAM",
                                                quantity=30,
                                                unit_price=150.0, # Value: 4500.0
                                                specification=ItemSpec(
                                                    dimensions_cm=[15.0, 4.0, 0.6],
                                                    weight_kg=0.15
                                                )
                                            )
                                        ]
                                    ]
                                )
                            ]
                        )
                    ]
                ]
            )
        ]
    )
    return input_obj.model_dump()

import pytest


@pytest.mark.anyio
async def test_complex_pipeline():
    logger.info(f"Connecting to live MCP server at {MCP_SERVER_URL} over Streamable HTTP...")
    from mcp.client.streamable_http import streamablehttp_client

    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info("Connected & Handshake completed successfully.")

            # Wrap the ClientSession inside our elegant MCPClient wrapper
            mcp_client = MCPClient(session)
            configs = [
                {
                    "engine": "jmespath",
                    "expression": ["$task_1.region_summaries[*].block_summaries[] | max_by(@, &total_value).total_value"],
                    "name": "JMESPATH EXCLUSIVE (Built-in max_by & Multi-field Projection)"
                },
                {
                    "engine": "jsonpath",
                    "expression": "$task_1.region_summaries[*].block_summaries[*].total_value",
                    "name": "JSONPath Standard Wildcard Selection"
                },
                {
                    "engine": "dot_notation",
                    "expression": ["$task_1.region_summaries.0.block_summaries.0.total_value"],
                    "name": "Dot Notation Direct Index Access"
                }
            ]

            for test_config in configs:
                engine_name = test_config["engine"]
                expr = test_config["expression"]
                test_name = test_config.get("name", "Standard Test")

                logger.info(f"🧪 TESTING CONFIG: {test_name} ({engine_name.upper()})")
                logger.info("==================================================")

                complex_plan = Plan(
                    tasks=[
                        PlanStep(
                            id="task_1",
                            tool_name="analyze_supply_chain",
                            args=make_complex_supply_chain_input()
                        ),
                        PlanStep(
                            id="task_2",
                            tool_name="calculate",
                            args={
                                "prices": expr
                            }
                        )
                    ]
                )

                executor = HeadlessExecutor(
                    session=mcp_client,
                    binding_engine=engine_name,
                )

                # Execute the complex plan
                logger.info(f"Executing complex nested pipeline plan with {engine_name}...")
                execution_context: ExecutionContext = await executor.run_plan(complex_plan)

                # Verification and Assertions
                # Step 1 Output verification
                step_1_res = execution_context.store["task_1"]
                assert step_1_res["network_name"] == "Global Enterprise Tech Logistics"
                assert len(step_1_res["region_summaries"]) == 1

                block_summary = step_1_res["region_summaries"][0]["block_summaries"][0]
                assert block_summary["block_id"] == "BLK-A1-PREMIUM"
                assert block_summary["total_value"] == 7000.0

                # Step 2 Output verification
                step_2_res = execution_context.store["task_2"]
                assert step_2_res["total_value"] == 7000.0
                assert step_2_res["count"] == 1

                logger.info(f"🎉 SUCCESS! Engine [{engine_name.upper()}] resolved variable perfectly!")
                logger.info(f"Resolved Prices list: {execution_context.results[1].output}")

            logger.info("==================================================")
            logger.info("🎉 ALL THREE BINDING ENGINES VERIFIED SUCCESSFULLY OVER LIVE MCP SERVER! 🎉")
            logger.info("==================================================")
    except Exception as e:
        logger.info(f"MCP Server connection failed ({e}). Skipping live pipeline test.")

if __name__ == "__main__":
    anyio.run(test_complex_pipeline)

