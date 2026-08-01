from fastmcp import FastMCP
import src.mcp.tools.business_tools as tools
from src.mcp.schema.models import *

mcp = FastMCP("agent-server")

@mcp.tool()
def search(input: SearchInput) -> SearchOutput:
    return tools.search_products(input)

@mcp.tool()
def convert_currency(input: ConvertCurrencyInput) -> ConvertCurrencyOutput:
    return tools.convert_currency(input)

@mcp.tool()
def apply_discount(input: ApplyDiscountInput) -> ApplyDiscountOutput:
    return tools.apply_discount(input)

@mcp.tool()
def compare_data(input: CompareInput) -> CompareOutput:
    return tools.compare_products(input)

@mcp.tool()
def calculate(input: CalculateInput) -> CalculateOutput:
    return tools.calculate_total_value(input)

@mcp.tool()
def analyze_supply_chain(input: SupplyChainInput) -> SupplyChainOutput:
    return tools.analyze_supply_chain(input)

@mcp.tool()
def process_org_structure(input: OrgStructureInput) -> OrgStructureOutput:
    return tools.process_org_structure(input)

@mcp.tool()
def evaluate_nested_curriculum(input: CurriculumInput) -> CurriculumOutput:
    return tools.evaluate_nested_curriculum(input)



if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import anyio
    from mcp.server.streamable_http import StreamableHTTPServerTransport

    transport = StreamableHTTPServerTransport(mcp_session_id="agent-session", is_json_response_enabled=True)

    app = Starlette(
        routes=[
            Mount("/mcp", app=transport.handle_request),
            Mount("/", app=transport.handle_request),
        ]
    )

    async def run_server():
        print("==================================================", flush=True)
        print("   Starting MCP Streamable HTTP Server...", flush=True)
        print("   Listening at: http://127.0.0.1:8000/mcp", flush=True)
        print("   Press Ctrl+C to stop the server.", flush=True)
        print("==================================================", flush=True)
        async with transport.connect() as (read_stream, write_stream):
            async with anyio.create_task_group() as tg:
                config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
                server = uvicorn.Server(config)
                tg.start_soon(server.serve)
                await anyio.sleep(0.1)

                await mcp._mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp._mcp_server.create_initialization_options()
                )

    anyio.run(run_server)