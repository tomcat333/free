from tests.conftest import add_item


def test_home_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "前沿雷达" in resp.text


def test_item_layers_and_dispatch(client, session):
    item = add_item(session, title="Sparse MoE World Model")
    home = client.get("/")
    assert "Sparse MoE World Model" in home.text
    page = client.get(f"/items/{item.id}")
    assert page.status_code == 200
    assert "深度介绍" in page.text
    assert "全过程" in page.text
    assert "远程试跑" in page.text

    intro = client.post(f"/api/items/{item.id}/intro")
    assert intro.status_code == 200
    assert intro.json()["intro"]

    deep = client.post(f"/api/items/{item.id}/deep-dive")
    assert deep.status_code == 200
    assert deep.json()["deep_dive"]

    dispatched = client.post(f"/api/items/{item.id}/dispatch")
    assert dispatched.status_code == 200
    body = dispatched.json()
    assert body["status"] == "prepared"
    assert body["pack"]["title"] == "Sparse MoE World Model"


def test_api_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["total_items"] == 0


def test_home_xray_track_filter(client, session):
    add_item(session, title="AI paper", kind="paper", url="https://example.com/ai", source_id="ai")
    add_item(
        session,
        title="CD-SAXS study",
        kind="pro_paper",
        source="arxiv_pro",
        url="https://example.com/pro",
        source_id="pro",
    )
    add_item(
        session,
        title="Rigaku news",
        kind="vendor",
        source="vendor",
        url="https://example.com/vendor",
        source_id="vendor",
    )
    home = client.get("/?track=xray")
    assert home.status_code == 200
    assert "专业·X射线" in home.text
    assert "CD-SAXS study" in home.text
    assert "Rigaku news" in home.text
    assert "AI paper" not in home.text
    vendors = client.get("/?kind=vendor")
    assert "Rigaku news" in vendors.text
    assert "CD-SAXS study" not in vendors.text
