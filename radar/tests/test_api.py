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
