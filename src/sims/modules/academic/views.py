"""Read-only mappings of the SQL views (kept off Base.metadata so Alembic never tries to create them)."""
from sqlalchemy import Column, MetaData, Numeric, SmallInteger, Table, Uuid

views_metadata = MetaData()

v_group_course = Table(
    "v_group_course", views_metadata,
    Column("group_id", Uuid), Column("academic_year_id", Uuid), Column("course", SmallInteger),
)

v_contract_balance = Table(
    "v_contract_balance", views_metadata,
    Column("contract_id", Uuid), Column("student_id", Uuid),
    Column("due_total", Numeric(12, 2)), Column("paid_total", Numeric(12, 2)), Column("debt", Numeric(12, 2)),
)
