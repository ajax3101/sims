from tests import factories as f

CONTRACT = {"number": "К-2026-001", "starts_on": "2026-09-01", "ends_on": "2030-06-30", "total_amount": "40000.00",
            "schedule": [{"due_date": "2000-09-15", "amount": "20000.00"}, {"due_date": "2999-02-15", "amount": "20000.00"}]}


async def _contract(client, session, **override):
    st = await f.student(session)
    resp = await client.post("/api/contracts", json={"student_id": str(st.id), **CONTRACT, **override})
    return st, resp


async def test_create_contract_with_schedule_and_balance(client, session):
    _, resp = await _contract(client, session)
    assert resp.status_code == 201, resp.text
    c = resp.json()
    assert (c["due_total"], c["paid_total"], c["debt"], len(c["schedule"])) == ("20000.00", "0.00", "20000.00", 2)


async def test_payment_reduces_debt(client, session):
    _, resp = await _contract(client, session)
    cid = resp.json()["id"]
    pay = await client.post(f"/api/contracts/{cid}/payments", json={"paid_on": "2000-09-10", "amount": "15000.00",
                                                                    "method": "bank", "external_ref": "PP-1"})
    assert pay.status_code == 201, pay.text
    c = (await client.get(f"/api/contracts/{cid}")).json()
    assert (c["paid_total"], c["debt"]) == ("15000.00", "5000.00")


async def test_schedule_exceeding_contract_total_is_422(client, session):
    _, resp = await _contract(client, session, total_amount="30000.00")
    assert resp.status_code == 422


async def test_duplicate_contract_number_is_409(client, session):
    await _contract(client, session)
    _, resp = await _contract(client, session)
    assert resp.status_code == 409


async def test_duplicate_payment_reference_is_409(client, session):
    _, resp = await _contract(client, session)
    cid = resp.json()["id"]
    body = {"paid_on": "2000-09-10", "amount": "100.00", "external_ref": "PP-9"}
    await client.post(f"/api/contracts/{cid}/payments", json=body)
    assert (await client.post(f"/api/contracts/{cid}/payments", json=body)).status_code == 409


async def test_terminate_contract(client, session):
    _, resp = await _contract(client, session)
    c = await client.patch(f"/api/contracts/{resp.json()['id']}", json={"status": "terminated"})
    assert (c.status_code, c.json()["status"]) == (200, "terminated")
