from sqlalchemy import text

from tests.conftest import alembic

EXPECTED_TABLES = {
    "education_level", "study_form", "org_unit", "specialty", "educational_program",
    "academic_year", "study_group",
    "staff", "curatorship",
    "student", "student_group_membership", "student_status_history", "student_document",
    "semester", "discipline", "group_discipline", "grade", "academic_debt",
    "contract", "payment_schedule_item", "payment",
    "import_batch", "import_issue",
}

TABLES_SQL = text(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name <> 'alembic_version'"
)


async def _tables(engine) -> set[str]:
    async with engine.connect() as conn:
        return set((await conn.execute(TABLES_SQL)).scalars())


async def test_upgrade_head_creates_full_schema(engine):
    assert await _tables(engine) == EXPECTED_TABLES


async def test_downgrade_base_removes_schema_and_upgrade_restores_it(engine):
    await alembic("downgrade", "base")
    try:
        assert await _tables(engine) == set()
    finally:
        await alembic("upgrade", "head")
    assert await _tables(engine) == EXPECTED_TABLES
