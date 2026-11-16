def test_snapshot_known_symbol(client):
    response = client.get("/snapshot/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "last_price" in data
    assert "last_seq" in data
    assert data["last_seq"] >= 0
    assert "reference_data" in data


def test_snapshot_unknown_symbol(client):
    response = client.get("/snapshot/UNKNOWN")
    assert response.status_code == 404
