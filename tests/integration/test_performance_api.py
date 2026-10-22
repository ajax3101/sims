from tests import factories as f


async def _plan(client, session, control_form="exam"):
    g = await f.group(session)
    st = await f.student(session, current_group_id=g.id)
    year = await f.academic_year(session, 2090)
    sem = (await client.post("/api/semesters", json={"academic_year_id": str(year.id), "number": 1})).json()
    disc = (await client.post("/api/disciplines", json={"name": "Вища математика", "code": f"VM-{st.id.hex[:6]}"})).json()
    gd = await client.post("/api/group-disciplines", json={
        "group_id": str(g.id), "discipline_id": disc["id"], "semester_id": sem["id"],
        "control_form": control_form, "credits_ects": "5.0"})
    assert gd.status_code == 201, gd.text
    return g, st, gd.json()


async def _grade(client, st, gd, kind, score, day="2090-12-20"):
    resp = await client.post("/api/grades", json={
        "student_id": str(st.id), "group_discipline_id": gd["id"], "kind": kind, "score": score, "graded_on": day})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _debts(client, st):
    return (await client.get(f"/api/students/{st.id}/performance")).json()["debts"]


async def test_duplicate_semester_is_409(client, session):
    year = await f.academic_year(session, 2091)
    body = {"academic_year_id": str(year.id), "number": 2}
    assert (await client.post("/api/semesters", json=body)).status_code == 201
    assert (await client.post("/api/semesters", json=body)).status_code == 409


async def test_group_curriculum_is_listed(client, session):
    g, _, gd = await _plan(client, session)
    items = (await client.get(f"/api/groups/{g.id}/disciplines")).json()
    assert [(i["id"], i["discipline"], i["control_form"], i["credits_ects"]) for i in items] == [
        (gd["id"], "Вища математика", "exam", "5.0")]


async def test_grade_derives_ects_and_national_from_score(client, session):
    _, st, gd = await _plan(client, session)
    g = await _grade(client, st, gd, "final", 85)
    assert (g["ects"], g["national"], g["attempt_no"]) == ("B", "good", 1)


async def test_failing_final_grade_opens_debt_and_successful_retake_closes_it(client, session):
    _, st, gd = await _plan(client, session)
    await _grade(client, st, gd, "final", 40)
    assert [(d["status"], d["opened_on"]) for d in await _debts(client, st)] == [("open", "2090-12-20")]

    await _grade(client, st, gd, "retake", 50, day="2091-01-10")   # still failing: debt stays open
    retake = await _grade(client, st, gd, "retake", 70, day="2091-01-20")
    assert retake["attempt_no"] == 2
    [debt] = await _debts(client, st)
    assert (debt["status"], debt["closed_on"]) == ("closed", "2091-01-20")


async def test_current_grades_never_open_debts(client, session):
    _, st, gd = await _plan(client, session)
    await _grade(client, st, gd, "current", 10)
    assert await _debts(client, st) == []


async def test_failed_pass_fail_credit_opens_debt(client, session):
    _, st, gd = await _plan(client, session, control_form="credit")
    g = await _grade(client, st, gd, "final", 59)
    assert (g["national"], [d["status"] for d in await _debts(client, st)]) == ("failed", ["open"])


async def test_schedule_retake_on_a_debt(client, session):
    _, st, gd = await _plan(client, session)
    await _grade(client, st, gd, "final", 20)
    [debt] = await _debts(client, st)
    resp = await client.patch(f"/api/academic-debts/{debt['id']}",
                              json={"status": "retake_scheduled", "retake_deadline": "2091-02-01"})
    assert (resp.status_code, resp.json()["status"], resp.json()["retake_deadline"]) == (200, "retake_scheduled", "2091-02-01")


async def test_debt_list_filters_by_group_and_status(client, session):
    g, st, gd = await _plan(client, session)
    await _grade(client, st, gd, "final", 20)
    body = (await client.get("/api/academic-debts", params={"group_id": str(g.id), "status": "open"})).json()
    assert [(d["student"]["id"], d["discipline"], d["group"]["code"]) for d in body["items"]] == [
        (str(st.id), "Вища математика", g.code)]
    assert (await client.get("/api/academic-debts", params={"group_id": str(g.id), "status": "closed"})).json()["total"] == 0


async def test_score_out_of_range_is_422(client, session):
    _, st, gd = await _plan(client, session)
    resp = await client.post("/api/grades", json={"student_id": str(st.id), "group_discipline_id": gd["id"],
                                                  "kind": "final", "score": 101, "graded_on": "2090-12-20"})
    assert resp.status_code == 422
