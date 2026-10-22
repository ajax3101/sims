from datetime import date
from decimal import Decimal

import pytest

from sims.models import (
    AcademicDebt, Contract, Curatorship, DebtStatus, Grade, GradeKind, Payment, PaymentScheduleItem,
)
from tests import factories as f

START = 2026  # course of a group = START - admission_year + entry_course


async def _world(session):
    """Two groups in the current year with five students; literal expectations below are derived by hand."""
    await f.academic_year(session, START, is_current=True)
    g1 = await f.group(session, code="6.G3.26-з-w1", admission_year=2026)            # course 1
    g2 = await f.group(session, code="6.G3.25-з-w2", admission_year=2025)            # course 2
    curator = await f.staff(session)
    session.add(Curatorship(group_id=g2.id, staff_id=curator.id, starts_on=date(2025, 9, 1)))
    s = {}
    for key, last, group, funding in [
        ("bad", "Бадя", g1, "budget"), ("bren", "Бренер", g1, "contract"),
        ("zin", "Зінов’єв", g2, "contract"), ("ach", "Ачкасов", g2, "budget"), ("yak", "Якименко", g2, None),
    ]:
        st = await f.student(session, last_name=last, full_name_norm=f"{last.casefold()} іван", funding=funding,
                             current_group_id=group.id)
        await f.membership(session, st, group, date(2025, 9, 1))
        s[key] = st
    s["bad"].record_book_no = "ЗК-777"
    gd = await f.group_discipline(session, g2)
    session.add(AcademicDebt(student_id=s["zin"].id, group_discipline_id=gd.id, opened_on=date(2026, 1, 25)))
    session.add(AcademicDebt(student_id=s["ach"].id, group_discipline_id=gd.id, opened_on=date(2026, 1, 25),
                             status=DebtStatus.CLOSED, closed_on=date(2026, 2, 10)))
    c = Contract(student_id=s["bren"].id, number="К-1", starts_on=date(2026, 9, 1), total_amount=Decimal("30000"))
    c.schedule = [PaymentScheduleItem(due_date=date(2000, 9, 1), amount=Decimal("15000"))]
    c.payments = [Payment(paid_on=date(2000, 9, 2), amount=Decimal("5000"))]
    session.add(c)
    await session.flush()
    return {"g1": g1, "g2": g2, "curator": curator, "gd": gd, **s}


def _names(body):
    return [i["last_name"] for i in body["items"]]


async def _list(client, **params):
    resp = await client.get("/api/students", params={"size": 200, **params})
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_default_order_is_by_name_with_total(client, session):
    await _world(session)
    body = await _list(client)
    assert (_names(body), body["total"]) == (["Ачкасов", "Бадя", "Бренер", "Зінов’єв", "Якименко"], 5)


async def test_sort_descending_and_by_course(client, session):
    await _world(session)
    assert _names(await _list(client, sort="-name"))[0] == "Якименко"
    assert _names(await _list(client, sort="course"))[:2] == ["Бадя", "Бренер"]


async def test_unknown_sort_field_is_422(client):
    assert (await client.get("/api/students", params={"sort": "password"})).status_code == 422


async def test_pagination(client, session):
    await _world(session)
    body = await _list(client, size=2, page=3)
    assert (_names(body), body["total"], body["page"]) == (["Якименко"], 5, 3)


@pytest.mark.parametrize("params, want", [
    ({"course": 2}, ["Ачкасов", "Зінов’єв", "Якименко"]),
    ({"funding": "contract"}, ["Бренер", "Зінов’єв"]),
    ({"has_academic_debt": "true"}, ["Зінов’єв"]),
    ({"has_academic_debt": "false"}, ["Ачкасов", "Бадя", "Бренер", "Якименко"]),
    ({"has_financial_debt": "true"}, ["Бренер"]),
    ({"q": "бад"}, ["Бадя"]),
    ({"q": "ЗІНОВ'ЄВ"}, ["Зінов’єв"]),
    ({"q": "ЗК-777"}, ["Бадя"]),
    ({"q": "%"}, []),
])
async def test_filters_and_search(client, session, params, want):
    await _world(session)
    assert _names(await _list(client, **params)) == want


async def test_filter_by_group_and_curator(client, session):
    w = await _world(session)
    assert _names(await _list(client, group_id=str(w["g1"].id))) == ["Бадя", "Бренер"]
    assert _names(await _list(client, curator_id=str(w["curator"].id))) == ["Ачкасов", "Зінов’єв", "Якименко"]


async def test_list_item_carries_group_course_and_debts(client, session):
    await _world(session)
    items = {i["last_name"]: i for i in (await _list(client))["items"]}
    assert (items["Бренер"]["group"]["code"], items["Бренер"]["course"], items["Бренер"]["financial_debt"]) == (
        "6.G3.26-з-w1", 1, "10000.00")
    assert (items["Зінов’єв"]["has_academic_debt"], items["Зінов’єв"]["financial_debt"]) == (True, "0.00")
    assert items["Бренер"]["specialty"] == {"code": "G3", "name": "Електрична інженерія"}


async def test_card_shows_profile_group_course_and_curator(client, session):
    w = await _world(session)
    card = (await client.get(f"/api/students/{w['zin'].id}")).json()
    assert (card["last_name"], card["group"]["code"], card["group"]["course"], card["group"]["curator"]["id"]) == (
        "Зінов’єв", "6.G3.25-з-w2", 2, str(w["curator"].id))


async def test_unknown_student_is_404(client):
    resp = await client.get("/api/students/0192f3f0-0000-7000-8000-000000000000")
    assert (resp.status_code, resp.json()["detail"]) == (404, "student not found")


async def test_performance_tab_groups_grades_by_semester_and_lists_debts(client, session):
    w = await _world(session)
    for kind, attempt, score, day in [(GradeKind.FINAL, 1, 40, 20), (GradeKind.RETAKE, 1, 75, 28)]:
        session.add(Grade(student_id=w["zin"].id, group_discipline_id=w["gd"].id, kind=kind, attempt_no=attempt,
                          score=score, graded_on=date(2026, 1, day)))
    await session.flush()
    perf = (await client.get(f"/api/students/{w['zin'].id}/performance")).json()
    [sem] = perf["semesters"]
    [disc] = sem["disciplines"]
    assert (sem["semester"], [g["score"] for g in disc["grades"]], disc["final"]["score"]) == (1, [40, 75], 75)
    assert [(d["status"], d["discipline"]) for d in perf["debts"]] == [("open", disc["discipline"])]


async def test_finance_tab_shows_contract_schedule_payments_and_balance(client, session):
    w = await _world(session)
    fin = (await client.get(f"/api/students/{w['bren'].id}/finance")).json()
    [c] = fin["contracts"]
    assert (c["number"], c["due_total"], c["paid_total"], c["debt"]) == ("К-1", "15000.00", "5000.00", "10000.00")
    assert ([p["amount"] for p in c["payments"]], [s["amount"] for s in c["schedule"]]) == (["5000.00"], ["15000.00"])
    assert fin["total_debt"] == "10000.00"


async def test_create_student_puts_them_in_the_group(client, session):
    w = await _world(session)
    resp = await client.post("/api/students", json={
        "last_name": "Нова", "first_name": "Марія", "patronymic": "Іванівна", "group_id": str(w["g1"].id),
        "funding": "budget", "enrolled_on": "2026-09-01", "contacts": {"phone": "+380501112233"}})
    assert resp.status_code == 201, resp.text
    sid = resp.json()["id"]
    assert "Нова" in _names(await _list(client, group_id=str(w["g1"].id)))
    hist = (await client.get(f"/api/students/{sid}/history")).json()
    assert [(m["group"]["code"], m["starts_on"], m["reason"]) for m in hist["memberships"]] == [
        ("6.G3.26-з-w1", "2026-09-01", "enrollment")]


async def test_patch_student_and_duplicate_tax_id_is_409(client, session):
    w = await _world(session)
    ok = await client.patch(f"/api/students/{w['bad'].id}", json={"tax_id": "1234567890", "first_name": "Петро"})
    assert (ok.status_code, ok.json()["first_name"]) == (200, "Петро")
    dup = await client.patch(f"/api/students/{w['bren'].id}", json={"tax_id": "1234567890"})
    assert dup.status_code == 409


async def test_status_change_is_recorded_in_history(client, session):
    w = await _world(session)
    resp = await client.post(f"/api/students/{w['bad'].id}/status",
                             json={"status": "academic_leave", "changed_on": "2026-10-01", "order_no": "123-с"})
    assert (resp.status_code, resp.json()["status"]) == (200, "academic_leave")
    hist = (await client.get(f"/api/students/{w['bad'].id}/history")).json()
    assert [(h["status"], h["changed_on"], h["order_no"]) for h in hist["status_history"]] == [
        ("academic_leave", "2026-10-01", "123-с")]
    assert _names(await _list(client, status="academic_leave")) == ["Бадя"]


async def test_same_status_again_is_422(client, session):
    w = await _world(session)
    resp = await client.post(f"/api/students/{w['bad'].id}/status", json={"status": "active", "changed_on": "2026-10-01"})
    assert resp.status_code == 422


async def test_transfer_closes_membership_and_moves_student(client, session):
    w = await _world(session)
    resp = await client.post(f"/api/students/{w['bad'].id}/transfer",
                             json={"group_id": str(w["g2"].id), "on": "2026-11-01", "order_ref": "45-к"})
    assert resp.status_code == 200, resp.text
    hist = (await client.get(f"/api/students/{w['bad'].id}/history")).json()
    assert [(m["group"]["code"], m["ends_on"], m["reason"]) for m in hist["memberships"]] == [
        ("6.G3.25-з-w2", None, "transfer"), ("6.G3.26-з-w1", "2026-11-01", "enrollment")]
    assert "Бадя" in _names(await _list(client, group_id=str(w["g2"].id)))


async def test_transfer_to_the_same_group_is_422(client, session):
    w = await _world(session)
    resp = await client.post(f"/api/students/{w['bad'].id}/transfer", json={"group_id": str(w["g1"].id), "on": "2026-11-01"})
    assert resp.status_code == 422
