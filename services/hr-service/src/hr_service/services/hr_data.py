"""Mock HR data generation using Faker."""

import logging

logger = logging.getLogger(__name__)

DEPARTMENTS = ["IT", "HR", "Finance", "Sales", "Operations", "Marketing"]
POSITIONS = {
    "IT": ["Software Engineer", "DevOps Engineer", "Data Analyst", "IT Manager", "CTO"],
    "HR": ["HR Manager", "Recruiter", "HR Specialist", "People Lead"],
    "Finance": ["Accountant", "Financial Analyst", "CFO", "Controller"],
    "Sales": ["Sales Manager", "Account Executive", "Sales Director"],
    "Operations": ["Operations Manager", "Logistics Coordinator", "COO"],
    "Marketing": ["Marketing Manager", "Content Specialist", "CMO"],
}


async def generate_seed_data(employee_count: int = 50) -> dict:
    """Generate realistic German mock HR data.

    Creates employees with:
    - German names (via Faker 'de_DE' locale)
    - Realistic department/position assignments
    - Salary bands per position
    - Vacation balances with history
    - Time tracking for last 30 days
    - 3-4 hierarchy levels in org chart
    """
    # TODO: Implement with Faker
    # from faker import Faker
    # fake = Faker("de_DE")
    logger.info("Seed data generation stub", extra={"target_count": employee_count})
    return {"employees_created": 0, "message": "Seed data stub — implementation pending"}
