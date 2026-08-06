# Unit tests for nested tools
from src.mcp.schema.models import (
    AcademicYearNode,
    AccreditationInfo,
    Address,
    AisleStorage,
    AssigneeProfile,
    ClassSection,
    CompanyProfile,
    ContactDetail,
    CourseModule,
    CurriculumInput,
    DivisionNode,
    InstructorProfile,
    ItemBatch,
    ItemSpec,
    LocationDetail,
    ManagerInfo,
    NetworkMetadata,
    OrgStructureInput,
    ProgramMeta,
    ProjectDetail,
    RegionNode,
    ScheduleSlot,
    SupplyChainInput,
    TaskNode,
    TeamLead,
    TeamUnit,
    WarehouseBlock,
)
from src.mcp.tools import business_tools as tools


def test_analyze_supply_chain_5_levels():
    input_data = SupplyChainInput(
        network_info=NetworkMetadata(network_name="Global Tech Supply", version="v2.0"), # Level 1 (Obj -> Obj)
        regions=[ # Level 1 -> Level 2 (Obj -> Array)
            RegionNode( # Level 2 (Array -> Obj)
                region_code="APAC-NORTH",
                warehouse_matrix=[ # Level 2 -> Level 3 (Obj -> Array -> Array)
                    [
                        WarehouseBlock( # Level 3 (Array -> Obj)
                            block_id="BLK-A1",
                            manager=ManagerInfo( # Level 3 (Obj -> Obj)
                                name="Alice Smith",
                                contact=ContactDetail(email="alice@tech.com", phone="+123456789") # Level 3 (Obj -> Obj)
                            ),
                            aisles=[ # Level 3 -> Level 4 (Obj -> Array)
                                AisleStorage( # Level 4 (Array -> Obj)
                                    aisle_id="AISLE-01",
                                    shelf_grid=[ # Level 4 -> Level 5 (Obj -> Array -> Array)
                                        [
                                            ItemBatch( # Level 5 (Array -> Obj)
                                                sku="SKU-MICRO-01",
                                                item_name="Microchip A1",
                                                quantity=5,
                                                unit_price=120.0,
                                                specification=ItemSpec( # Level 5 (Obj -> Obj)
                                                    dimensions_cm=[1.5, 1.5, 0.2], # Level 5 (Obj -> Array)
                                                    weight_kg=0.05
                                                )
                                            ),
                                            ItemBatch(
                                                sku="SKU-RAM-02",
                                                item_name="DDR5 RAM 16GB",
                                                quantity=50,
                                                unit_price=80.0,
                                                specification=ItemSpec(
                                                    dimensions_cm=[13.3, 3.0, 0.5],
                                                    weight_kg=0.1
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

    output = tools.analyze_supply_chain(input_data)
    assert output.network_name == "Global Tech Supply"
    assert output.total_regions == 1
    assert output.total_warehouses == 1
    assert output.total_items_count == 55
    assert output.total_inventory_value == (5 * 120.0) + (50 * 80.0)
    assert "SKU-MICRO-01" in output.low_stock_skus
    assert len(output.region_summaries) == 1
    assert output.region_summaries[0].region_code == "APAC-NORTH"


def test_process_org_structure_5_levels():
    input_data = OrgStructureInput(
        company_profile=CompanyProfile(
            company_name="Acme Corp",
            hq_address=Address(city="Tokyo", country="Japan")
        ),
        divisions=[
            DivisionNode(
                division_id="DIV-ENG",
                division_name="Engineering",
                team_matrix=[
                    [
                        TeamUnit(
                            team_id="TEAM-CORE",
                            lead=TeamLead(
                                name="Bob Jones",
                                contact=ContactDetail(email="bob@acme.com", phone="+81001122")
                            ),
                            projects=[
                                ProjectDetail(
                                    project_id="PRJ-AI",
                                    project_name="AI Engine",
                                    budget=150000.0,
                                    sprint_tasks=[
                                        [
                                            TaskNode(
                                                task_id="TASK-01",
                                                title="Design Architecture",
                                                estimated_hours=40.0,
                                                assignee=AssigneeProfile(
                                                    user_id="USR-101",
                                                    skills=["Python", "PyTorch", "Architecture"]
                                                )
                                            ),
                                            TaskNode(
                                                task_id="TASK-02",
                                                title="Implement Optimization",
                                                estimated_hours=25.0,
                                                assignee=AssigneeProfile(
                                                    user_id="USR-102",
                                                    skills=["C++", "CUDA"]
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

    output = tools.process_org_structure(input_data)
    assert output.company_name == "Acme Corp"
    assert output.total_divisions == 1
    assert output.total_teams == 1
    assert output.total_projects == 1
    assert output.total_org_budget == 150000.0
    assert output.total_work_hours == 65.0


def test_evaluate_nested_curriculum_5_levels():
    input_data = CurriculumInput(
        program_meta=ProgramMeta(
            program_code="CS-BS",
            accreditation=AccreditationInfo(agency="ABET", valid_until="2032-12-31")
        ),
        academic_years=[
            AcademicYearNode(
                year_number=1,
                semester_blocks=[
                    [
                        CourseModule(
                            course_code="CS101",
                            course_name="Intro to CS",
                            credits=4,
                            instructor=InstructorProfile(
                                name="Dr. Grace",
                                contact=ContactDetail(email="grace@university.edu", phone="+199988877")
                            ),
                            class_sections=[
                                ClassSection(
                                    section_id="SEC-01",
                                    timetable_grid=[
                                        [
                                            ScheduleSlot(
                                                room_number="R-101",
                                                location=LocationDetail(building="Science Hall", floor=2),
                                                enrolled_scores=[85.0, 92.5, 78.0, 90.0]
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

    output = tools.evaluate_nested_curriculum(input_data)
    assert output.program_code == "CS-BS"
    assert output.total_years == 1
    assert output.total_modules == 1
    assert output.total_credits == 4
    expected_avg = round((85.0 + 92.5 + 78.0 + 90.0) / 4, 2)
    assert output.overall_average_score == expected_avg


if __name__ == "__main__":
    test_analyze_supply_chain_5_levels()
    test_process_org_structure_5_levels()
    test_evaluate_nested_curriculum_5_levels()
    print("All nested tool tests passed successfully!")
