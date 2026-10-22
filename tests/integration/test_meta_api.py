from sims.core.config import get_settings


async def test_meta_reports_demo_flag_off_by_default(client):
    assert (await client.get("/api/meta")).json() == {"demo": False}


async def test_meta_reports_demo_flag_from_settings(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo", True)
    assert (await client.get("/api/meta")).json() == {"demo": True}
