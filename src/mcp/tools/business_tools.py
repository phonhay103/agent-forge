
from src.mcp.schema.models import *


def search_products(input: SearchInput) -> SearchOutput:
    """Search for products in catalog."""
    mock_db = {
        "iphone": [
            Product(name="iPhone 15 Pro Max", price=1199.0, rating=4.9, category="Smartphones"),
            Product(name="iPhone 15 Pro", price=999.0, rating=4.8, category="Smartphones"),
            Product(name="iPhone 15", price=799.0, rating=4.6, category="Smartphones"),
            Product(name="iPhone 14", price=699.0, rating=4.4, category="Smartphones"),
            Product(name="iPhone SE", price=429.0, rating=4.1, category="Smartphones")
        ],
        "laptop": [
            Product(name="MacBook Pro 16", price=2499.0, rating=4.9, category="Laptops"),
            Product(name="MacBook Air M3", price=1099.0, rating=4.7, category="Laptops"),
            Product(name="Dell XPS 15", price=1599.0, rating=4.5, category="Laptops"),
            Product(name="ThinkPad X1 Carbon", price=1429.0, rating=4.6, category="Laptops")
        ]
    }
    key = input.product_name.lower()
    results = []
    for k, v in mock_db.items():
        if k in key or key in k:
            results.extend(v)
    if not results:
        for items in mock_db.values():
            results.extend([p for p in items if key in p.name.lower()])
    return SearchOutput(items=results, currency="USD")

def convert_currency(input: ConvertCurrencyInput) -> ConvertCurrencyOutput:
    """Convert product prices to target currency (VND, EUR, JPY, GBP)."""
    rates = {
        "VND": 25400.0,
        "EUR": 0.92,
        "JPY": 155.0,
        "GBP": 0.78,
        "USD": 1.0
    }
    rate = rates.get(input.target_currency.upper(), 1.0)
    converted = []
    for p in input.products:
        p_copy = p.model_copy()
        p_copy.price = round(p.price * rate, 2)
        p_copy.currency = input.target_currency.upper()
        converted.append(p_copy)
    return ConvertCurrencyOutput(converted_products=converted, target_currency=input.target_currency.upper())

def apply_discount(input: ApplyDiscountInput) -> ApplyDiscountOutput:
    """Apply discount percentage to products."""
    discount_factor = 1.0 - (input.discount_percent / 100.0)
    discounted = []
    for p in input.products:
        p_copy = p.model_copy()
        p_copy.price = round(p.price * discount_factor, 2)
        discounted.append(p_copy)
    return ApplyDiscountOutput(discounted_products=discounted, discount_percent=input.discount_percent)

def compare_products(input: CompareInput) -> CompareOutput:
    """Compare products and identify cheapest, highest rated, and best value."""
    if not input.products:
        return CompareOutput()
    cheapest = min(input.products, key=lambda p: p.price)
    highest_rated = max(input.products, key=lambda p: p.rating)
    best_value = max(input.products, key=lambda p: p.rating / max(p.price, 1.0))
    return CompareOutput(
        best_value_product=best_value,
        cheapest_product=cheapest,
        highest_rated_product=highest_rated
    )

def calculate_total_value(input: CalculateInput) -> CalculateOutput:
    """Calculate total sum and count of prices."""
    return CalculateOutput(total_value=sum(input.prices), count=len(input.prices))

def analyze_supply_chain(input: SupplyChainInput) -> SupplyChainOutput:
    """Analyze a deeply nested 5-tier supply chain network and aggregate statistics."""
    total_warehouses = 0
    total_inventory_value = 0.0
    total_items_count = 0
    low_stock_skus = []
    region_summaries = []

    for region in input.regions:
        reg_blocks_count = 0
        reg_items_count = 0
        reg_value = 0.0
        block_summaries = []

        for row in region.warehouse_matrix:
            for block in row:
                reg_blocks_count += 1
                total_warehouses += 1
                block_qty = 0
                block_val = 0.0

                for aisle in block.aisles:
                    for shelf_row in aisle.shelf_grid:
                        for batch in shelf_row:
                            batch_val = batch.quantity * batch.unit_price
                            block_qty += batch.quantity
                            block_val += batch_val
                            if batch.quantity < 10 and batch.sku not in low_stock_skus:
                                low_stock_skus.append(batch.sku)

                reg_items_count += block_qty
                reg_value += block_val
                block_summaries.append(
                    BlockSummary(
                        block_id=block.block_id,
                        total_quantity=block_qty,
                        total_value=round(block_val, 2),
                        manager_name=block.manager.name
                    )
                )

        total_inventory_value += reg_value
        total_items_count += reg_items_count
        region_summaries.append(
            RegionSummary(
                region_code=region.region_code,
                total_blocks=reg_blocks_count,
                total_items=reg_items_count,
                regional_value=round(reg_value, 2),
                block_summaries=block_summaries
            )
        )

    return SupplyChainOutput(
        network_name=input.network_info.network_name,
        total_regions=len(input.regions),
        total_warehouses=total_warehouses,
        total_inventory_value=round(total_inventory_value, 2),
        total_items_count=total_items_count,
        low_stock_skus=low_stock_skus,
        region_summaries=region_summaries
    )


def process_org_structure(input: OrgStructureInput) -> OrgStructureOutput:
    """Process a deeply nested enterprise org structure & project matrix."""
    total_teams = 0
    total_projects = 0
    total_org_budget = 0.0
    total_work_hours = 0.0
    division_summaries = []

    for division in input.divisions:
        div_teams = 0
        div_budget = 0.0
        project_summaries = []

        for domain_row in division.team_matrix:
            for team in domain_row:
                div_teams += 1
                total_teams += 1

                for proj in team.projects:
                    total_projects += 1
                    div_budget += proj.budget
                    proj_tasks = 0
                    proj_hours = 0.0

                    for sprint in proj.sprint_tasks:
                        for task in sprint:
                            proj_tasks += 1
                            proj_hours += task.estimated_hours

                    total_work_hours += proj_hours
                    project_summaries.append(
                        ProjectSummary(
                            project_id=proj.project_id,
                            project_name=proj.project_name,
                            budget=proj.budget,
                            total_tasks=proj_tasks,
                            total_hours=proj_hours
                        )
                    )

        total_org_budget += div_budget
        division_summaries.append(
            DivisionSummary(
                division_id=division.division_id,
                division_name=division.division_name,
                total_teams=div_teams,
                total_budget=round(div_budget, 2),
                project_summaries=project_summaries
            )
        )

    return OrgStructureOutput(
        company_name=input.company_profile.company_name,
        total_divisions=len(input.divisions),
        total_teams=total_teams,
        total_projects=total_projects,
        total_org_budget=round(total_org_budget, 2),
        total_work_hours=round(total_work_hours, 2),
        division_summaries=division_summaries
    )


def evaluate_nested_curriculum(input: CurriculumInput) -> CurriculumOutput:
    """Evaluate a 5-tier nested academic curriculum matrix and score metrics."""
    total_modules = 0
    total_credits = 0
    all_scores = []
    module_summaries = []

    for year_node in input.academic_years:
        for sem_row in year_node.semester_blocks:
            for module in sem_row:
                total_modules += 1
                total_credits += module.credits
                mod_scores = []
                mod_slots = 0

                for sec in module.class_sections:
                    for day_row in sec.timetable_grid:
                        for slot in day_row:
                            mod_slots += 1
                            mod_scores.extend(slot.enrolled_scores)

                all_scores.extend(mod_scores)
                mod_avg = round(sum(mod_scores) / len(mod_scores), 2) if mod_scores else 0.0
                module_summaries.append(
                    ModuleSummary(
                        course_code=module.course_code,
                        course_name=module.course_name,
                        credits=module.credits,
                        average_score=mod_avg,
                        total_slots=mod_slots
                    )
                )

    overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return CurriculumOutput(
        program_code=input.program_meta.program_code,
        total_years=len(input.academic_years),
        total_modules=total_modules,
        total_credits=total_credits,
        overall_average_score=overall_avg,
        module_summaries=module_summaries
    )



