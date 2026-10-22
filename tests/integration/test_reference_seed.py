from sqlalchemy import text


async def _rows(session, sql: str) -> set[tuple]:
    return set(map(tuple, (await session.execute(text(sql))).all()))


async def test_education_levels_seeded_with_nqf_levels(session):
    assert await _rows(session, "SELECT code, nqf_level FROM education_level") == {
        ("bachelor", 6), ("master", 7), ("phd", 8),
    }


async def test_study_forms_seeded_part_time_marked_z(session):
    assert await _rows(session, "SELECT code, group_marker FROM study_form") == {
        ("full_time", None), ("part_time", "з"), ("dual", None),
    }


async def test_specialties_seeded_for_both_classifiers(session):
    rows = await _rows(session, "SELECT classifier, code, field_code FROM specialty")
    assert rows == {
        ("2015", "136", "13"), ("2015", "141", "14"), ("2015", "144", "14"), ("2015", "174", "17"),
        ("2015", "183", "18"), ("2015", "192", "19"), ("2015", "263", "26"),
        ("2024", "G2", "G"), ("2024", "G3", "G"), ("2024", "G4", "G"), ("2024", "G5", "G"),
        ("2024", "G7", "G"), ("2024", "G10", "G"), ("2024", "G19", "G"), ("2024", "J4", "J"),
    }


async def test_old_specialties_map_to_2024_successors(session):
    mapping = await _rows(
        session,
        "SELECT o.code, n.code FROM specialty o JOIN specialty n ON n.id = o.successor_id "
        "WHERE o.classifier = '2015'",
    )
    assert mapping == {
        ("136", "G10"), ("141", "G3"), ("144", "G4"), ("174", "G7"),
        ("183", "G2"), ("192", "G19"), ("263", "J4"),
    }


async def test_specialty_names_are_sentence_case(session):
    name = (await session.execute(text("SELECT name FROM specialty WHERE code = 'G3'"))).scalar_one()
    assert name == "Електрична інженерія"
