from datetime import date

from tests import factories as f


async def test_create_2024_specialty_derives_field_code(client):
    resp = await client.post("/api/specialties", json={"classifier": "2024", "code": "G21", "name": "Тестова інженерія"})
    assert resp.status_code == 201, resp.text
    s = resp.json()
    assert (s["code"], s["field_code"], s["groups_count"], s["students_count"]) == ("G21", "G", 0, 0)


async def test_create_2015_specialty_with_successor(client):
    new = (await client.post("/api/specialties", json={"classifier": "2024", "code": "G22", "name": "Нова"})).json()
    resp = await client.post("/api/specialties", json={"classifier": "2015", "code": "199", "name": "Стара", "successor_id": new["id"]})
    assert resp.status_code == 201, resp.text
    assert (resp.json()["field_code"], resp.json()["successor_id"]) == ("19", new["id"])


async def test_duplicate_specialty_code_is_409(client):
    body = {"classifier": "2024", "code": "G23", "name": "Перша"}
    await client.post("/api/specialties", json=body)
    assert (await client.post("/api/specialties", json=body)).status_code == 409


async def test_code_must_match_its_classifier(client):
    bad = [{"classifier": "2024", "code": "136", "name": "x"}, {"classifier": "2015", "code": "G3", "name": "x"}]
    assert [(await client.post("/api/specialties", json=b)).status_code for b in bad] == [422, 422]


async def test_patch_specialty_renames(client):
    s = (await client.post("/api/specialties", json={"classifier": "2024", "code": "G24", "name": "Чернетка"})).json()
    resp = await client.patch(f"/api/specialties/{s['id']}", json={"name": "Чистова"})
    assert (resp.status_code, resp.json()["name"], resp.json()["code"]) == (200, "Чистова", "G24")


async def test_list_counts_groups_and_current_students(client, session):
    g = await f.group(session)  # factory groups use the seeded G3
    st = await f.student(session, current_group_id=g.id)
    await f.membership(session, st, g, date(2025, 9, 1))
    rows = {(s["classifier"], s["code"]): s for s in (await client.get("/api/specialties")).json()}
    assert rows[("2024", "G3")]["groups_count"] >= 1 and rows[("2024", "G3")]["students_count"] >= 1
    assert rows[("2015", "136")]["successor_code"] == "G10"
