from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Domain Models ---
class Product(BaseModel):
    name: str
    price: float
    category: str = "Electronics"
    rating: float = 4.5
    currency: str = "USD"

# --- Tool Input/Output Models ---
class SearchInput(BaseModel):
    product_name: str = Field(description="Name or keyword of product to search")

class SearchOutput(BaseModel):
    items: List[Product]
    currency: str = "USD"

class ConvertCurrencyInput(BaseModel):
    products: List[Product]
    target_currency: str = Field(description="Target currency code: VND, EUR, JPY, GBP")

class ConvertCurrencyOutput(BaseModel):
    converted_products: List[Product]
    target_currency: str

class ApplyDiscountInput(BaseModel):
    products: List[Product]
    discount_percent: float = Field(description="Discount percentage between 0 and 100, e.g., 10 for 10% off")

class ApplyDiscountOutput(BaseModel):
    discounted_products: List[Product]
    discount_percent: float

class CompareInput(BaseModel):
    products: List[Product]

class CompareOutput(BaseModel):
    best_value_product: Optional[Product] = None
    cheapest_product: Optional[Product] = None
    highest_rated_product: Optional[Product] = None

class CalculateInput(BaseModel):
    prices: List[float]

class CalculateOutput(BaseModel):
    total_value: float
    count: int

# --- Deeply Nested Models (3-5 Levels with Alternating Obj/Array Patterns) ---

# --- 1. Supply Chain Network Models ---
class ItemSpec(BaseModel):
    dimensions_cm: List[float] = Field(description="List of dimensions [length, width, height] - Object to Array")
    weight_kg: float = Field(description="Weight in kg")

class ItemBatch(BaseModel):
    sku: str = Field(description="Stock Keeping Unit identifier")
    item_name: str = Field(description="Product name")
    quantity: int = Field(description="Quantity in stock")
    unit_price: float = Field(description="Price per unit")
    specification: ItemSpec = Field(description="Item technical specs - Object to Object")

class AisleStorage(BaseModel):
    aisle_id: str = Field(description="Aisle identifier")
    shelf_grid: List[List[ItemBatch]] = Field(
        description="2D layout matrix of item batches [shelf_tier][section] - Object to Array of Arrays of Objects"
    )

class ContactDetail(BaseModel):
    email: str = Field(default="contact@example.com")
    phone: str = Field(default="+1-555-0199")

class ManagerInfo(BaseModel):
    name: str = Field(description="Manager name")
    contact: ContactDetail = Field(description="Contact details - Object to Object")

class WarehouseBlock(BaseModel):
    block_id: str = Field(description="Block identifier")
    manager: ManagerInfo = Field(description="Block manager - Object to Object")
    aisles: List[AisleStorage] = Field(description="List of aisles in block - Object to Array of Objects")

class RegionNode(BaseModel):
    region_code: str = Field(description="Region identifier, e.g. US-WEST, APAC")
    warehouse_matrix: List[List[WarehouseBlock]] = Field(
        description="2D grid matrix of warehouse blocks [zone_row][zone_col] - Object to Array of Arrays of Objects"
    )

class NetworkMetadata(BaseModel):
    network_name: str = Field(description="Supply chain network name")
    version: str = Field(default="v1.0", description="Schema version")

class SupplyChainInput(BaseModel):
    network_info: NetworkMetadata = Field(description="Network metadata - Object to Object")
    regions: List[RegionNode] = Field(description="List of regional warehouse nodes - Object to Array of Objects")

class BlockSummary(BaseModel):
    block_id: str
    total_quantity: int
    total_value: float
    manager_name: str

class RegionSummary(BaseModel):
    region_code: str
    total_blocks: int
    total_items: int
    regional_value: float
    block_summaries: List[BlockSummary]

class SupplyChainOutput(BaseModel):
    network_name: str
    total_regions: int
    total_warehouses: int
    total_inventory_value: float
    total_items_count: int
    low_stock_skus: List[str]
    region_summaries: List[RegionSummary]


# --- 2. Org Structure & Project Matrix Models ---
class AssigneeProfile(BaseModel):
    user_id: str = Field(description="User ID")
    skills: List[str] = Field(description="Skills list - Object to Array")

class TaskNode(BaseModel):
    task_id: str = Field(description="Task ID")
    title: str = Field(description="Task title")
    estimated_hours: float = Field(description="Estimated duration in hours")
    assignee: AssigneeProfile = Field(description="Assigned member profile - Object to Object")

class ProjectDetail(BaseModel):
    project_id: str = Field(description="Project ID")
    project_name: str = Field(description="Project name")
    budget: float = Field(description="Project budget")
    sprint_tasks: List[List[TaskNode]] = Field(
        description="2D matrix of tasks [sprint_idx][priority_level] - Object to Array of Arrays of Objects"
    )

class TeamLead(BaseModel):
    name: str = Field(description="Lead name")
    contact: ContactDetail = Field(description="Contact info - Object to Object")

class TeamUnit(BaseModel):
    team_id: str = Field(description="Team ID")
    lead: TeamLead = Field(description="Team lead profile - Object to Object")
    projects: List[ProjectDetail] = Field(description="Projects managed by team - Object to Array of Objects")

class DivisionNode(BaseModel):
    division_id: str = Field(description="Division ID")
    division_name: str = Field(description="Division name")
    team_matrix: List[List[TeamUnit]] = Field(
        description="2D matrix of teams [domain_idx][tier_level] - Object to Array of Arrays of Objects"
    )

class Address(BaseModel):
    city: str = Field(default="San Francisco")
    country: str = Field(default="USA")

class CompanyProfile(BaseModel):
    company_name: str = Field(description="Company name")
    hq_address: Address = Field(description="HQ Address - Object to Object")

class OrgStructureInput(BaseModel):
    company_profile: CompanyProfile = Field(description="Company profile - Object to Object")
    divisions: List[DivisionNode] = Field(description="List of organization divisions - Object to Array of Objects")

class ProjectSummary(BaseModel):
    project_id: str
    project_name: str
    budget: float
    total_tasks: int
    total_hours: float

class DivisionSummary(BaseModel):
    division_id: str
    division_name: str
    total_teams: int
    total_budget: float
    project_summaries: List[ProjectSummary]

class OrgStructureOutput(BaseModel):
    company_name: str
    total_divisions: int
    total_teams: int
    total_projects: int
    total_org_budget: float
    total_work_hours: float
    division_summaries: List[DivisionSummary]


# --- 3. Academic Curriculum & Schedule Matrix Models ---
class LocationDetail(BaseModel):
    building: str = Field(default="Hall A")
    floor: int = Field(default=1)

class ScheduleSlot(BaseModel):
    room_number: str = Field(description="Room number")
    location: LocationDetail = Field(description="Building location - Object to Object")
    enrolled_scores: List[float] = Field(description="List of student test scores - Object to Array")

class ClassSection(BaseModel):
    section_id: str = Field(description="Section ID")
    timetable_grid: List[List[ScheduleSlot]] = Field(
        description="2D schedule matrix [day_of_week][time_block] - Object to Array of Arrays of Objects"
    )

class InstructorProfile(BaseModel):
    name: str = Field(description="Instructor name")
    contact: ContactDetail = Field(description="Contact detail - Object to Object")

class CourseModule(BaseModel):
    course_code: str = Field(description="Course code, e.g., CS101")
    course_name: str = Field(description="Course title")
    credits: int = Field(description="Credit hours")
    instructor: InstructorProfile = Field(description="Instructor profile - Object to Object")
    class_sections: List[ClassSection] = Field(description="List of class sections - Object to Array of Objects")

class AcademicYearNode(BaseModel):
    year_number: int = Field(description="Year index (1, 2, 3, 4)")
    semester_blocks: List[List[CourseModule]] = Field(
        description="2D matrix of modules [semester_idx][track_idx] - Object to Array of Arrays of Objects"
    )

class AccreditationInfo(BaseModel):
    agency: str = Field(default="ABET")
    valid_until: str = Field(default="2030-12-31")

class ProgramMeta(BaseModel):
    program_code: str = Field(description="Program code")
    accreditation: AccreditationInfo = Field(description="Accreditation details - Object to Object")

class CurriculumInput(BaseModel):
    program_meta: ProgramMeta = Field(description="Program metadata - Object to Object")
    academic_years: List[AcademicYearNode] = Field(description="Academic year nodes - Object to Array of Objects")

class ModuleSummary(BaseModel):
    course_code: str
    course_name: str
    credits: int
    average_score: float
    total_slots: int

class CurriculumOutput(BaseModel):
    program_code: str
    total_years: int
    total_modules: int
    total_credits: int
    overall_average_score: float
    module_summaries: List[ModuleSummary]



