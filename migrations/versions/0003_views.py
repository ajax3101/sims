"""derived views: group course per academic year, contract balance

Course and payment debt are computed, never stored: yearly promotion needs no
UPDATE, and debt cannot drift from the payments it is derived from.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW v_group_course AS
        SELECT g.id AS group_id,
               y.id AS academic_year_id,
               (y.start_year - g.admission_year + g.entry_course)::smallint AS course
        FROM study_group g
        JOIN academic_year y
          ON y.start_year >= g.admission_year
         AND y.start_year - g.admission_year + g.entry_course <= 6
         AND (g.study_end IS NULL OR y.starts_on < g.study_end)
    """)
    op.execute("""
        CREATE VIEW v_contract_balance AS
        SELECT c.id AS contract_id,
               c.student_id,
               COALESCE(s.due_total, 0)::numeric(12, 2) AS due_total,
               COALESCE(p.paid_total, 0)::numeric(12, 2) AS paid_total,
               GREATEST(COALESCE(s.due_total, 0) - COALESCE(p.paid_total, 0), 0)::numeric(12, 2) AS debt
        FROM contract c
        LEFT JOIN LATERAL (
            SELECT sum(amount) AS due_total FROM payment_schedule_item
            WHERE contract_id = c.id AND due_date <= current_date
        ) s ON true
        LEFT JOIN LATERAL (
            SELECT sum(amount) AS paid_total FROM payment WHERE contract_id = c.id
        ) p ON true
    """)


def downgrade() -> None:
    op.execute("DROP VIEW v_contract_balance")
    op.execute("DROP VIEW v_group_course")
