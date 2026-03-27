"""Coverage-focused tests for HR data generation, seeding, and routes."""

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service import main as hr_main
from hr_service.database import Employee, SalaryRecord, TimeEntryRecord, VacationRecord
from hr_service.database import connection as hr_connection
from hr_service.database.seed import seed_database
from hr_service.services import hr_data


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2026, 3, 27)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None) -> "FixedDateTime":
        return cls(2026, 3, 27, 12, 0, 0, tzinfo=tz or UTC)


@pytest.fixture()
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hr_data, "date", FixedDate)
    monkeypatch.setattr(hr_data, "datetime", FixedDateTime)


@pytest.mark.asyncio
async def test_hr_helpers_and_seed_data_are_deterministic(fixed_clock: None) -> None:
    assert hr_data._build_employee_id(7) == "emp-007"
    assert hr_data._net_monthly_from_gross(120_000) == 5_800.0

    business_days = list(hr_data._business_days(7))
    assert len(business_days) == 5
    assert all(day.weekday() < 5 for day in business_days)
    assert business_days[0] == FixedDate(2026, 3, 27)

    first = await hr_data.generate_seed_data(employee_count=12)
    second = await hr_data.generate_seed_data(employee_count=12)

    assert first == second
    assert len(first["employees"]) == 12
    assert {employee["department"] for employee in first["employees"]} == set(hr_data.DEPARTMENTS)
    assert first["employees"][0]["position"] == "CTO"
    assert first["employees"][6]["position"] == "IT Manager"
    assert first["employees"][6]["manager_id"] == "emp-001"
    assert first["employees"][11]["manager_id"] == "emp-006"
    assert len(first["vacations"]) == 12
    assert len(first["salaries"]) == 12
    assert first["time_entries"]


@pytest.mark.asyncio
async def test_seed_database_populates_and_is_idempotent(tmp_path, fixed_clock: None) -> None:
    db_path = tmp_path / "hr.sqlite"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with session_factory() as session:
            summary = await seed_database(session, employee_count=12)
            assert summary["employees_created"] == 12
            assert summary["vacation_records_created"] == 12
            assert summary["salary_records_created"] == 12
            assert summary["time_entries_created"] > 0

            employee_rows = (await session.exec(select(Employee))).all()
            salary_rows = (await session.exec(select(SalaryRecord))).all()
            vacation_rows = (await session.exec(select(VacationRecord))).all()
            time_rows = (await session.exec(select(TimeEntryRecord))).all()

            assert len(employee_rows) == 12
            assert len(salary_rows) == 12
            assert len(vacation_rows) == 12
            assert len(time_rows) == summary["time_entries_created"]
            assert employee_rows[0].id == "emp-001"

            repeat = await seed_database(session, employee_count=12)
            assert repeat == {"employees_created": 0, "message": "Database already seeded"}
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_hr_database_connection_lifecycle(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "hr-connection.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    original_url = hr_connection.settings.database_url

    monkeypatch.setattr(hr_connection.settings, "database_url", db_url)
    await hr_connection.close_database()
    await hr_connection.ensure_database_ready()

    session_factory = hr_connection.get_session_factory()
    async with session_factory() as session:
        result = await session.exec(select(Employee))
        assert len(result.all()) == 50

    async for session in hr_connection.get_session():
        assert session is not None
        break

    await hr_connection.close_database()
    monkeypatch.setattr(hr_connection.settings, "database_url", original_url)
    with pytest.raises(RuntimeError):
        hr_connection.get_session_factory()


def test_hr_routes_cover_filters_missing_employee_and_lifespan() -> None:
    client = TestClient(hr_main.app)

    health = client.get("/health")
    assert health.status_code == 200

    it_employees = client.get("/api/v1/employees", params={"department": "IT"})
    assert it_employees.status_code == 200
    assert it_employees.json()
    assert all(employee["department"] == "IT" for employee in it_employees.json())

    employee = client.get("/api/v1/employees/emp-001")
    assert employee.status_code == 200
    assert employee.json()["id"] == "emp-001"

    missing = client.get("/api/v1/employees/emp-999")
    assert missing.status_code == 404

    salary = client.get("/api/v1/employees/emp-001/salary")
    assert salary.status_code == 200
    assert salary.json()["employee_id"] == "emp-001"

    timetracking = client.get("/api/v1/employees/emp-001/timetracking")
    assert timetracking.status_code == 200
    assert timetracking.json()["employee_id"] == "emp-001"

    vacation = client.get("/api/v1/employees/emp-001/vacation")
    assert vacation.status_code == 200
    assert vacation.json()["remaining_days"] >= 0

    org_chart = client.get("/api/v1/org/IT")
    assert org_chart.status_code == 200
    assert isinstance(org_chart.json(), list)
