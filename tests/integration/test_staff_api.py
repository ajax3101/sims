from tests import factories as f


async def _staff(client, last_name="Коваленко"):
    resp = await client.post("/api/staff", json={"last_name": last_name, "first_name": "Олена", "patronymic": "Іванівна",
                                                 "position": "доцент", "email": "kovalenko@example.com"})
    assert resp.status_code == 201
    return resp.json()


async def test_create_and_search_staff(client):
    s = await _staff(client)
    assert s["full_name"] == "Коваленко Олена Іванівна"
    await _staff(client, "Петренко")
    body = (await client.get("/api/staff", params={"q": "ковал"})).json()
    assert [x["id"] for x in body["items"]] == [s["id"]]


async def test_assigning_new_curator_closes_previous_curatorship(client, session):
    g = await f.group(session)
    a, b = await _staff(client, "Перший"), await _staff(client, "Другий")

    r1 = await client.post(f"/api/groups/{g.id}/curator", json={"staff_id": a["id"], "starts_on": "2026-09-01"})
    r2 = await client.post(f"/api/groups/{g.id}/curator", json={"staff_id": b["id"], "starts_on": "2026-10-01"})
    assert (r1.status_code, r2.status_code) == (201, 201)

    history = (await client.get(f"/api/groups/{g.id}/curators")).json()
    assert [(h["staff"]["id"], h["starts_on"], h["ends_on"]) for h in history] == [
        (b["id"], "2026-10-01", None), (a["id"], "2026-09-01", "2026-10-01"),
    ]
    assert (await client.get(f"/api/groups/{g.id}")).json()["curator"]["id"] == b["id"]


async def test_curator_start_before_current_start_is_409(client, session):
    g = await f.group(session)
    a, b = await _staff(client, "Перший"), await _staff(client, "Другий")
    await client.post(f"/api/groups/{g.id}/curator", json={"staff_id": a["id"], "starts_on": "2026-09-01"})
    resp = await client.post(f"/api/groups/{g.id}/curator", json={"staff_id": b["id"], "starts_on": "2026-08-01"})
    assert resp.status_code == 409


async def test_staff_list_shows_groups_currently_curated(client, session):
    g = await f.group(session)
    a = await _staff(client, "Куратор")
    await client.post(f"/api/groups/{g.id}/curator", json={"staff_id": a["id"], "starts_on": "2026-09-01"})
    item = next(x for x in (await client.get("/api/staff", params={"q": "Куратор"})).json()["items"] if x["id"] == a["id"])
    assert item["curated_groups"] == [{"id": str(g.id), "code": g.code}]
