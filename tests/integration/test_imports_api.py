from httpx import ASGITransport, AsyncClient

from sims.core.db import get_session
from sims.main import create_app
from tests import docx_builder as b


async def _client(session):
    app = create_app()

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_upload_roster_returns_report_and_batch_is_retrievable(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(rows=[("1", "Бадя Віталій Олегович", ""), ("2", "123", "Б")]))
    async with await _client(session) as client:
        resp = await client.post("/api/imports", files=[("files", ("список.docx", path.read_bytes()))])
        assert resp.status_code == 200
        [report] = resp.json()
        assert (report["source_filename"], report["students_created"], report["errors"], report["warnings"]) == (
            "список.docx", 1, 1, 1)

        batch = await client.get(f"/api/imports/{report['batch_id']}")
        assert batch.status_code == 200
        body = batch.json()
        assert (body["status"], body["source_filename"]) == ("done", "список.docx")
        assert sorted(i["code"] for i in body["issues"]) == ["funding_missing", "invalid_name"]


async def test_upload_of_unsupported_type_is_415(session):
    async with await _client(session) as client:
        resp = await client.post("/api/imports", files=[("files", ("notes.txt", b"hello"))])
    assert resp.status_code == 415


async def test_unknown_batch_is_404(session):
    async with await _client(session) as client:
        resp = await client.get("/api/imports/0192f3f0-0000-7000-8000-000000000000")
    assert (resp.status_code, resp.json()) == (404, {"detail": "import batch not found"})
