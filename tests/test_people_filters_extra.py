def test_people_min_only_max_only_and_no_next_token(client, seed_households):
    # minAge only
    r = client.get("/people", params={"type": "family", "ageMin": 5, "limit": 50})
    assert r.status_code == 200
    data = r.json()
    assert data["nextPageToken"] is None
    for it in data["items"]:
        assert any(a >= 5 for a in it["childAges"])

    # maxAge only
    r = client.get("/people", params={"type": "family", "ageMax": 6})
    assert r.status_code == 200
    for it in r.json()["items"]:
        assert any(a <= 6 for a in it["childAges"])

def test_people_neighborhood_case_and_search(client, seed_households):
    r = client.get("/people", params={"neighborhood": "bayHILL", "search": "sm"})
    assert r.status_code == 200
    for it in r.json()["items"]:
        assert it["neighborhood"].lower() == "bayhill"
