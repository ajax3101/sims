from datetime import date

from sqlalchemy import select

from sims.models import EducationLevel, OrgUnit, OrgUnitKind, Specialty, StudyForm
from tests import factories as f


def _current_start_year(today: date) -> int:
    return today.year if today.month >= 9 else today.year - 1


async def _refs(session):
    unit = OrgUnit(kind=OrgUnitKind.INSTITUTE, name="ІННІ")
    session.add(unit)
    await session.flush()
    spec = (await session.execute(select(Specialty).where(Specialty.code == "G3"))).scalar_one()
    return {"specialty_id": str(spec.id), "org_unit_id": str(unit.id), "level": "bachelor", "form": "part_time"}


async def test_dictionaries_expose_seeded_reference_data(client):
    body = (await client.get("/api/dictionaries")).json()
    assert {l["code"] for l in body["levels"]} == {"bachelor", "master", "phd"}
    assert {x["code"] for x in body["forms"]} == {"full_time", "part_time", "dual"}
    assert ("2015", "136") in {(s["classifier"], s["code"]) for s in body["specialties"]}


async def test_marking_a_year_current_unmarks_the_previous_one(client):
    a = (await client.post("/api/academic-years", json={"start_year": 2071, "is_current": True})).json()
    assert (a["label"], a["starts_on"], a["ends_on"]) == ("2071/2072", "2071-09-01", "2072-06-30")
    b = (await client.post("/api/academic-years", json={"start_year": 2072, "is_current": True})).json()

    assert (await client.get("/api/academic-years/current")).json()["id"] == b["id"]
    years = {y["start_year"]: y["is_current"] for y in (await client.get("/api/academic-years")).json()}
    assert (years[2071], years[2072]) == (False, True)


async def test_current_year_falls_back_to_the_one_containing_today(client):
    start = _current_start_year(date.today())
    await client.post("/api/academic-years", json={"start_year": start})
    assert (await client.get("/api/academic-years/current")).json()["start_year"] == start


async def test_create_group_derives_cohort_fields_from_code(client, session):
    resp = await client.post("/api/groups", json={"code": "6.G3.26-з-c2", **await _refs(session)})
    assert resp.status_code == 201
    g = resp.json()
    assert (g["code_norm"], g["admission_year"], g["entry_course"], g["is_shortened"]) == ("6.G3.26-з-с2", 2026, 2, True)


async def test_duplicate_group_code_is_409(client, session):
    refs = await _refs(session)
    await client.post("/api/groups", json={"code": "6.G3.26-з", **refs})
    resp = await client.post("/api/groups", json={"code": "6.G3.26-з", **refs})
    assert resp.status_code == 409


async def test_invalid_group_code_is_422(client, session):
    resp = await client.post("/api/groups", json={"code": "X-26", **await _refs(session)})
    assert resp.status_code == 422


async def test_patch_group_changes_only_given_fields(client, session):
    g = (await client.post("/api/groups", json={"code": "6.G3.26-з", **await _refs(session)})).json()
    resp = await client.patch(f"/api/groups/{g['id']}", json={"study_end": "2030-06-30"})
    assert (resp.json()["study_end"], resp.json()["code"]) == ("2030-06-30", "6.G3.26-з")


async def test_unknown_group_is_404(client):
    resp = await client.get("/api/groups/0192f3f0-0000-7000-8000-000000000000")
    assert (resp.status_code, resp.json()) == (404, {"detail": "group not found"})


async def test_group_list_shows_current_course_and_filters_by_it(client, session):
    start = _current_start_year(date.today())
    await client.post("/api/academic-years", json={"start_year": start, "is_current": True})
    g1 = await f.group(session, code=f"6.G3.{start % 100}-з-t1", admission_year=start)
    g2 = await f.group(session, code=f"6.G3.{(start - 1) % 100}-з-t2", admission_year=start - 1)

    body = (await client.get("/api/groups", params={"course": 2, "size": 200})).json()
    ids = {g["id"]: g["course"] for g in body["items"]}
    assert ids == {str(g2.id): 2}
    assert body["total"] == 1

    one = (await client.get(f"/api/groups/{g1.id}")).json()
    assert one["course"] == 1


async def test_group_list_paginates(client, session):
    for i in range(3):
        await f.group(session, code=f"6.G3.25-pg{i}")
    body = (await client.get("/api/groups", params={"q": "pg", "size": 2, "page": 2})).json()
    assert (body["total"], body["page"], body["size"], len(body["items"])) == (3, 2, 2, 1)


async def test_create_department_under_institute(client, session):
    refs = await _refs(session)
    resp = await client.post("/api/org-units", json={
        "kind": "department", "name": "Кафедра електротехніки", "parent_id": refs["org_unit_id"]})
    assert resp.status_code == 201
    units = {u["name"]: u["parent_id"] for u in (await client.get("/api/dictionaries")).json()["org_units"]}
    assert units["Кафедра електротехніки"] == refs["org_unit_id"]
