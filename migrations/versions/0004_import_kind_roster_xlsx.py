"""import_batch.kind: add roster_xlsx

Revision ID: 0004
Revises: 0003
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CK = op.f("ck_import_batch_import_kind")  # final name: skip the naming convention


def upgrade() -> None:
    op.drop_constraint(CK, "import_batch", type_="check")
    op.create_check_constraint(
        CK, "import_batch", "kind IN ('roster_docx', 'roster_xlsx', 'debts_xlsx', 'contracts_xlsx')"
    )


def downgrade() -> None:
    op.execute("DELETE FROM import_issue WHERE batch_id IN (SELECT id FROM import_batch WHERE kind = 'roster_xlsx')")
    op.execute("DELETE FROM import_batch WHERE kind = 'roster_xlsx'")
    op.drop_constraint(CK, "import_batch", type_="check")
    op.create_check_constraint(CK, "import_batch", "kind IN ('roster_docx', 'debts_xlsx', 'contracts_xlsx')")
