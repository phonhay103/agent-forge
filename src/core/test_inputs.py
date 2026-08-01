from pydantic import BaseModel, Field
from typing import List

class TestCase(BaseModel):
    id: str = Field(description="Unique identifier for the test case")
    name: str = Field(description="Short title or scenario name")
    category: str = Field(description="Category of complexity: basic, intermediate, complex")
    description: str = Field(description="Detailed explanation of what this test case tests")
    query: str = Field(description="The natural language prompt/task input for the Planner")

class TestSuite(BaseModel):
    suite_name: str = "MCP Core Planner & Engine Test Suite"
    test_cases: List[TestCase]

TEST_SUITE = TestSuite(
    test_cases=[
        TestCase(
            id="TC-01",
            name="Basic Search, Filter & Extract",
            category="basic",
            description="Searches for iPhone models, filters those above 800 USD, and extracts their prices.",
            query="Tìm iPhone, lọc các sản phẩm có giá trên 800 USD, sau đó trích xuất danh sách giá."
        ),
        TestCase(
            id="TC-02",
            name="Multi-Currency Conversion & Sorting",
            category="intermediate",
            description="Searches for laptops, converts USD prices to VND, and sorts descending by price.",
            query="Tìm laptop, quy đổi giá từ USD sang VND, sau đó sắp xếp danh sách laptop theo giá giảm dần."
        ),
        TestCase(
            id="TC-03",
            name="Discount Application & Price Comparison",
            category="intermediate",
            description="Searches for iPhones, applies a 10% discount, and compares to find cheapest and best value.",
            query="Tìm sản phẩm iPhone, áp dụng giảm giá 10% cho tất cả sản phẩm, sau đó so sánh các sản phẩm để tìm sản phẩm có giá rẻ nhất và giá trị tốt nhất."
        ),
        TestCase(
            id="TC-04",
            name="Categorization & Aggregate Statistics",
            category="complex",
            description="Searches for laptops, categorizes them by price tiers, extracts prices, and calculates full statistical metrics (min, max, average, sum).",
            query="Tìm laptop, phân loại chúng theo phân khúc giá (Budget, Mid-Range, Premium), trích xuất giá của các máy, và tính toán số liệu thống kê (giá trung bình, cao nhất, thấp nhất, tổng giá trị)."
        ),
        TestCase(
            id="TC-05",
            name="End-to-End Business Pipeline (Search -> Filter -> Discount -> Convert -> Format)",
            category="complex",
            description="Complex 5-step pipeline: Search iPhones -> Filter > $700 -> Apply 15% discount -> Convert prices to EUR -> Format final report in Markdown.",
            query="Tìm iPhone, lọc các máy có giá lớn hơn 700 USD, áp dụng mã giảm giá 15%, chuyển đổi giá các máy sau giảm giá sang đồng EUR, và tạo báo cáo tổng hợp dạng markdown."

        ),
        TestCase(
            id="TC-06",
            name="Deeply Nested Supply Chain Analysis (5-Level Nesting)",
            category="deep_nested",
            description="Analyzes a 5-tier supply chain network with alternating object-object, object-array, array-array, array-object nesting (Network -> Regions -> Warehouse Grid -> Aisles -> Shelf Items).",
            query="Phân tích mạng lưới chuỗi cung ứng lồng 5 tầng (GlobalNetwork -> Regions -> Warehouse Matrix -> Aisles -> Shelf Batches) để tính tổng giá trị kho, tổng số lượng hàng và tìm danh sách các SKU sắp hết hàng."
        ),
        TestCase(
            id="TC-07",
            name="Deeply Nested Org Structure & Project Matrix (5-Level Nesting)",
            category="deep_nested",
            description="Processes a 5-tier enterprise org structure with alternating object-object, object-array, array-array, array-object nesting (Company -> Divisions -> Team Grid -> Projects -> Sprint Task Matrix).",
            query="Xử lý cấu trúc tổ chức doanh nghiệp lồng 5 tầng (Company -> Divisions -> Team Matrix -> Projects -> Sprint Tasks) để tính tổng ngân sách, tổng số giờ làm việc và thống kê quy mô dự án."
        ),
        TestCase(
            id="TC-08",
            name="Deeply Nested Curriculum Matrix Evaluation (5-Level Nesting)",
            category="deep_nested",
            description="Evaluates a 5-tier academic curriculum matrix with alternating object-object, object-array, array-array, array-object nesting (Program -> Academic Years -> Semester Course Matrix -> Class Sections -> Timetable Schedule Grid).",
            query="Đánh giá chương trình đào tạo lồng 5 tầng (Program -> Academic Years -> Semester Course Matrix -> Class Sections -> Timetable Schedule Grid) để tính điểm trung bình toàn chương trình, tổng số tín chỉ và số suất học."
        )
,
        TestCase(
            id="TC-09",
            name="Built-In Engine JMESPath Variable Resolution (No Filtering Tool)",
            category="jmespath_engine",
            description="Tests the engine's built-in JMESPath variable parsing when passing outputs between steps without an intermediate filtering tool (e.g. $step_1.results[?price > `800`]).",
            query="Tìm kiếm sản phẩm iPhone, sau đó truyền trực tiếp kết quả đã lọc qua JMESPath nâng cao $step_1.results[?price > `800`] vào bước quy đổi tiền tệ mà không dùng tool lọc rời."
        ),
        TestCase(
            id="TC-10",
            name="Built-In JMESPath Matrix Flattening & Deep Reference Resolution",
            category="jmespath_engine",
            description="Evaluates 5-tier supply chain data in step 1, then uses built-in engine JMESPath resolution ($step_1.region_summaries[*].block_summaries[] | [?total_value > `1000`]) directly in step 2 input.",
            query="Chạy phân tích chuỗi cung ứng lồng 5 tầng ở step 1, sau đó dùng cú pháp JMESPath cố định trong engine $step_1.region_summaries[*].block_summaries[] | [?total_value > `1000`] để trích xuất các block có giá trị cao truyền vào bước tạo báo cáo."
        ),
        TestCase(
            id="TC-11",
            name="Built-In JMESPath Multi-Field Projection & In-Place Transformation",
            category="jmespath_engine",
            description="Processes 5-tier enterprise org structure, then resolves dynamic JMESPath references ($step_1.division_summaries | max_by(@, &total_budget)) in-place without needing a schema mapper tool.",
            query="Xử lý cấu trúc tổ chức 5 tầng ở step 1, sau đó dùng biểu thức JMESPath $step_1.division_summaries | max_by(@, &total_budget) để lấy ra phòng ban có ngân sách lớn nhất truyền vào bước tính toán tiếp theo."
        )
    ]
)
