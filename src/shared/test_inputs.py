
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    __test__ = False
    id: str = Field(description="Unique identifier for the test case")
    name: str = Field(description="Short title or scenario name")
    category: str = Field(description="Category of complexity: basic, intermediate, complex")
    description: str = Field(description="Detailed explanation of what this test case tests")
    query: str = Field(description="The natural language prompt/task input for the Planner")

class TestSuite(BaseModel):
    __test__ = False
    suite_name: str = "MCP Core Planner & Engine Test Suite"
    test_cases: list[TestCase]

TEST_SUITE = TestSuite(
    test_cases=[
        TestCase(
            id="TC-01",
            name="Basic Search, Filter & Extract",
            category="basic",
            description="Searches for iPhone models, filters those above 800 USD, and extracts their prices.",
            query="Search for iPhones, filter products priced over 800 USD, then extract the list of prices."
        ),
        TestCase(
            id="TC-02",
            name="Multi-Currency Conversion & Sorting",
            category="intermediate",
            description="Searches for laptops, converts USD prices to VND, and sorts descending by price.",
            query="Search for laptops, convert prices from USD to VND, then sort the laptops by price descending."
        ),
        TestCase(
            id="TC-03",
            name="Discount Application & Price Comparison",
            category="intermediate",
            description="Searches for iPhones, applies a 10% discount, and compares to find cheapest and best value.",
            query="Search for iPhone products, apply a 10% discount to all products, then compare products to find the cheapest and best value options."
        ),
        TestCase(
            id="TC-04",
            name="Categorization & Aggregate Statistics",
            category="complex",
            description="Searches for laptops, categorizes them by price tiers, extracts prices, and calculates full statistical metrics (min, max, average, sum).",
            query="Search for laptops, categorize them by price tiers (Budget, Mid-Range, Premium), extract prices, and calculate aggregate statistics (average, max, min, total value)."
        ),
        TestCase(
            id="TC-05",
            name="End-to-End Business Pipeline (Search -> Filter -> Discount -> Convert -> Format)",
            category="complex",
            description="Complex 5-step pipeline: Search iPhones -> Filter > $700 -> Apply 15% discount -> Convert prices to EUR -> Format final report in Markdown.",
            query="Search for iPhones, filter items with price over 700 USD, apply a 15% discount code, convert discounted prices to EUR, and create a markdown summary report."
        ),
        TestCase(
            id="TC-06",
            name="Deeply Nested Supply Chain Analysis (5-Level Nesting)",
            category="deep_nested",
            description="Analyzes a 5-tier supply chain network with alternating object-object, object-array, array-array, array-object nesting (Network -> Regions -> Warehouse Grid -> Aisles -> Shelf Items).",
            query="Analyze a 5-tier nested supply chain network (GlobalNetwork -> Regions -> Warehouse Matrix -> Aisles -> Shelf Batches) to calculate total warehouse value, total inventory count, and identify low stock SKUs."
        ),
        TestCase(
            id="TC-07",
            name="Deeply Nested Org Structure & Project Matrix (5-Level Nesting)",
            category="deep_nested",
            description="Processes a 5-tier enterprise org structure with alternating object-object, object-array, array-array, array-object nesting (Company -> Divisions -> Team Grid -> Projects -> Sprint Task Matrix).",
            query="Process a 5-tier nested enterprise organizational structure (Company -> Divisions -> Team Matrix -> Projects -> Sprint Tasks) to calculate total budget, total working hours, and summarize project scale."
        ),
        TestCase(
            id="TC-08",
            name="Deeply Nested Curriculum Matrix Evaluation (5-Level Nesting)",
            category="deep_nested",
            description="Evaluates a 5-tier academic curriculum matrix with alternating object-object, object-array, array-array, array-object nesting (Program -> Academic Years -> Semester Course Matrix -> Class Sections -> Timetable Schedule Grid).",
            query="Evaluate a 5-tier nested academic curriculum (Program -> Academic Years -> Semester Course Matrix -> Class Sections -> Timetable Schedule Grid) to calculate overall program GPA, total credits, and total available seats."
        ),
        TestCase(
            id="TC-09",
            name="Built-In Engine JMESPath Variable Resolution (No Filtering Tool)",
            category="jmespath_engine",
            description="Tests the engine's built-in JMESPath variable parsing when passing outputs between steps without an intermediate filtering tool (e.g. $step_1.results[?price > `800`]).",
            query="Search for iPhone products, then pass filtered results directly via advanced JMESPath $step_1.results[?price > `800`] into the currency conversion step without using a separate filter tool."
        ),
        TestCase(
            id="TC-10",
            name="Built-In JMESPath Matrix Flattening & Deep Reference Resolution",
            category="jmespath_engine",
            description="Evaluates 5-tier supply chain data in step 1, then uses built-in engine JMESPath resolution ($step_1.region_summaries[*].block_summaries[] | [?total_value > `1000`]) directly in step 2 input.",
            query="Run 5-tier supply chain analysis in step 1, then use fixed engine JMESPath syntax $step_1.region_summaries[*].block_summaries[] | [?total_value > `1000`] to extract high-value blocks into the report generation step."
        ),
        TestCase(
            id="TC-11",
            name="Built-In JMESPath Multi-Field Projection & In-Place Transformation",
            category="jmespath_engine",
            description="Processes 5-tier enterprise org structure, then resolves dynamic JMESPath references ($step_1.division_summaries | max_by(@, &total_budget)) in-place without needing a schema mapper tool.",
            query="Process 5-tier organizational structure in step 1, then use JMESPath expression $step_1.division_summaries | max_by(@, &total_budget) to extract the division with the largest budget and pass it to the next calculation step."
        )
    ]
)
