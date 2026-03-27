"""Database models for the HR service."""

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Employee(SQLModel, table=True):
    id: str = Field(primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    department: str = Field(index=True)
    position: str
    manager_id: str | None = Field(default=None, foreign_key="employee.id", index=True)
    pay_grade: str
    created_at: datetime
    updated_at: datetime


class SalaryRecord(SQLModel, table=True):
    employee_id: str = Field(primary_key=True, foreign_key="employee.id")
    gross_annual: float
    net_monthly: float
    currency: str = "EUR"
    pay_grade: str


class VacationRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: str = Field(foreign_key="employee.id", index=True)
    year: int = Field(index=True)
    total_days: int
    used_days: int
    remaining_days: int


class TimeEntryRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    employee_id: str = Field(foreign_key="employee.id", index=True)
    entry_date: date = Field(index=True)
    hours_worked: float
    project: str | None = None
