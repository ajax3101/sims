"""seed reference data: education levels, study forms, specialties (2015 → 2024)

Specialties are the ones found in the source rosters; successor links pair an
old code with the new one that carries the same educational programs there.

Revision ID: 0002
Revises: 0001
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEVELS = [
    ("bachelor", 6, "Бакалавр"),
    ("master", 7, "Магістр"),
    ("phd", 8, "Доктор філософії"),
]
FORMS = [
    ("full_time", "Денна", None),
    ("part_time", "Заочна", "з"),
    ("dual", "Дуальна", None),
]
SPECIALTIES_2024 = [
    ("G2", "Технології захисту навколишнього середовища"),
    ("G3", "Електрична інженерія"),
    ("G4", "Енерговиробництво"),
    ("G5", "Електроніка, електронні комунікації, приладобудування та радіотехніка"),
    ("G7", "Автоматизація, комп’ютерно-інтегровані технології та робототехніка"),
    ("G10", "Металургія"),
    ("G19", "Будівництво та цивільна інженерія"),
    ("J4", "Охорона праці"),
]
# (old code, name, successor code)
SPECIALTIES_2015 = [
    ("136", "Металургія", "G10"),
    ("141", "Електроенергетика, електротехніка та електромеханіка", "G3"),
    ("144", "Теплоенергетика", "G4"),
    ("174", "Автоматизація, комп’ютерно-інтегровані технології та робототехніка", "G7"),
    ("183", "Технології захисту навколишнього середовища", "G2"),
    ("192", "Будівництво та цивільна інженерія", "G19"),
    ("263", "Цивільна безпека", "J4"),
]

level_t = sa.table("education_level", sa.column("id"), sa.column("code"), sa.column("nqf_level"), sa.column("name"))
form_t = sa.table("study_form", sa.column("id"), sa.column("code"), sa.column("name"), sa.column("group_marker"))
spec_t = sa.table(
    "specialty", sa.column("id"), sa.column("classifier"), sa.column("code"),
    sa.column("name"), sa.column("field_code"), sa.column("successor_id"),
)


def upgrade() -> None:
    op.bulk_insert(level_t, [{"id": uuid.uuid7(), "code": c, "nqf_level": n, "name": nm} for c, n, nm in LEVELS])
    op.bulk_insert(form_t, [{"id": uuid.uuid7(), "code": c, "name": nm, "group_marker": m} for c, nm, m in FORMS])

    new_ids = {code: uuid.uuid7() for code, _ in SPECIALTIES_2024}
    op.bulk_insert(spec_t, [
        {"id": new_ids[code], "classifier": "2024", "code": code, "name": name,
         "field_code": code[0], "successor_id": None}
        for code, name in SPECIALTIES_2024
    ])
    op.bulk_insert(spec_t, [
        {"id": uuid.uuid7(), "classifier": "2015", "code": code, "name": name,
         "field_code": code[:2], "successor_id": new_ids[succ]}
        for code, name, succ in SPECIALTIES_2015
    ])


def downgrade() -> None:
    op.execute(spec_t.delete().where(spec_t.c.classifier == "2015"))
    op.execute(spec_t.delete().where(spec_t.c.code.in_([c for c, _ in SPECIALTIES_2024])))
    op.execute(form_t.delete().where(form_t.c.code.in_([c for c, _, _ in FORMS])))
    op.execute(level_t.delete().where(level_t.c.code.in_([c for c, _, _ in LEVELS])))
