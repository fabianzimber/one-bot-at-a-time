"""Mock HR data generation using Faker."""

import logging
import random
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta

from faker import Faker

logger = logging.getLogger(__name__)

DEPARTMENTS = ["IT", "HR", "Finance", "Sales", "Operations", "Marketing"]
POSITIONS = {
    "IT": ["CTO", "IT Manager", "Software Engineer", "DevOps Engineer", "Data Analyst"],
    "HR": ["People Lead", "HR Manager", "Recruiter", "HR Specialist"],
    "Finance": ["CFO", "Controller", "Financial Analyst", "Accountant"],
    "Sales": ["Sales Director", "Sales Manager", "Account Executive"],
    "Operations": ["COO", "Operations Manager", "Logistics Coordinator"],
    "Marketing": ["CMO", "Marketing Manager", "Content Specialist"],
}
PAY_GRADES = {
    "CTO": ("E6", 132000),
    "CFO": ("E6", 128000),
    "COO": ("E6", 126000),
    "CMO": ("E6", 122000),
    "People Lead": ("E5", 98000),
    "Sales Director": ("E5", 96000),
    "IT Manager": ("E5", 92000),
    "HR Manager": ("E4", 76000),
    "Controller": ("E4", 78000),
    "Sales Manager": ("E4", 72000),
    "Operations Manager": ("E4", 70000),
    "Marketing Manager": ("E4", 69000),
    "Software Engineer": ("E3", 64000),
    "DevOps Engineer": ("E3", 67000),
    "Data Analyst": ("E3", 61000),
    "Recruiter": ("E2", 52000),
    "HR Specialist": ("E2", 50000),
    "Financial Analyst": ("E3", 60000),
    "Accountant": ("E2", 51000),
    "Account Executive": ("E2", 56000),
    "Logistics Coordinator": ("E2", 47000),
    "Content Specialist": ("E2", 48000),
}
PROJECTS = ["Kandidatenplattform", "Payroll", "SAP-Rollout", "Staffing Hub", "Internal Ops", "CRM Migration"]


def _build_employee_id(index: int) -> str:
    return f"emp-{index:03d}"


def _net_monthly_from_gross(gross_annual: float) -> float:
    return round(gross_annual * 0.58 / 12, 2)


def _business_days(last_n_days: int) -> Iterable[date]:
    today = date.today()
    for offset in range(last_n_days):
        current = today - timedelta(days=offset)
        if current.weekday() < 5:
            yield current


async def generate_seed_data(employee_count: int = 50) -> dict:
    """Generate deterministic German mock data for the HR service."""
    seed = 42
    rng = random.Random(seed)
    Faker.seed(seed)
    fake = Faker("de_DE")

    employees: list[dict] = []
    salaries: list[dict] = []
    vacations: list[dict] = []
    time_entries: list[dict] = []

    now = datetime.now(UTC)
    employee_index = 1
    department_managers: dict[str, str] = {}
    managers_by_department: dict[str, list[str]] = {department: [] for department in DEPARTMENTS}

    for department in DEPARTMENTS:
        position = POSITIONS[department][0]
        employee_id = _build_employee_id(employee_index)
        first_name = fake.first_name()
        last_name = fake.last_name()
        pay_grade, gross_annual = PAY_GRADES[position]
        manager_id = None

        employees.append(
            {
                "id": employee_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name}.{last_name}@trenkwalder.example".lower().replace(" ", "-"),
                "department": department,
                "position": position,
                "manager_id": manager_id,
                "pay_grade": pay_grade,
                "created_at": now,
                "updated_at": now,
            }
        )
        salaries.append(
            {
                "employee_id": employee_id,
                "gross_annual": float(gross_annual),
                "net_monthly": _net_monthly_from_gross(float(gross_annual)),
                "currency": "EUR",
                "pay_grade": pay_grade,
            }
        )
        department_managers[department] = employee_id
        managers_by_department[department].append(employee_id)
        employee_index += 1

    while employee_index <= employee_count:
        department = DEPARTMENTS[(employee_index - 1) % len(DEPARTMENTS)]
        choices = POSITIONS[department][1:]
        position = rng.choice(choices)
        employee_id = _build_employee_id(employee_index)
        manager_id = rng.choice(managers_by_department[department])
        first_name = fake.first_name()
        last_name = fake.last_name()
        pay_grade, base_gross = PAY_GRADES[position]
        gross_annual = float(base_gross + rng.randint(-3500, 4500))

        employees.append(
            {
                "id": employee_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name}.{last_name}@trenkwalder.example".lower().replace(" ", "-"),
                "department": department,
                "position": position,
                "manager_id": manager_id,
                "pay_grade": pay_grade,
                "created_at": now,
                "updated_at": now,
            }
        )
        salaries.append(
            {
                "employee_id": employee_id,
                "gross_annual": gross_annual,
                "net_monthly": _net_monthly_from_gross(gross_annual),
                "currency": "EUR",
                "pay_grade": pay_grade,
            }
        )
        if position.endswith("Manager") or position in {"People Lead", "Sales Director"}:
            managers_by_department[department].append(employee_id)

        employee_index += 1

    current_year = date.today().year
    for employee in employees:
        total_days = 30 if employee["department"] in {"IT", "HR", "Finance"} else 28
        used_days = rng.randint(2, min(total_days - 4, 18))
        vacations.append(
            {
                "employee_id": employee["id"],
                "year": current_year,
                "total_days": total_days,
                "used_days": used_days,
                "remaining_days": total_days - used_days,
            }
        )

        for workday in _business_days(30):
            if rng.random() < 0.12:
                continue
            hours = round(rng.uniform(6.5, 8.5), 2)
            time_entries.append(
                {
                    "employee_id": employee["id"],
                    "entry_date": workday,
                    "hours_worked": hours,
                    "project": rng.choice(PROJECTS),
                }
            )

    summary = {
        "employees": employees,
        "salaries": salaries,
        "vacations": vacations,
        "time_entries": time_entries,
        "seed": seed,
    }
    logger.info(
        "Seed data generated",
        extra={
            "employees_created": len(employees),
            "vacation_records_created": len(vacations),
            "time_entries_created": len(time_entries),
        },
    )
    return summary
