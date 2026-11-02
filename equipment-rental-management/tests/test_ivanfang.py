# ============================================================
# Ivan Fang: tests for equipment and checkout features
# ============================================================
# Table B features covered in this file:
#   1. List all equipment            GET    /equipment
#   2. Add equipment                 POST   /equipment
#   3. View one equipment item       GET    /equipment/<id>
#   4. Update equipment              PUT    /equipment/<id>
#   5. Delete equipment              DELETE /equipment/<id>
#   6. Mark equipment in/out of service  PATCH /equipment/<id>/status
#   7. Check one item's availability GET    /equipment/<id>/availability
#  13. Check out equipment           POST   /rentals
#
# Tests marked "DEFECT" are expected to fail against the reference app.
# Each one states the requirement (Table A ID) that supports the expected
# behaviour.
# ============================================================


def create_equipment(client, **overrides):
    payload = {"name": "Kayak", "category": "Water", "total_units": 3}
    payload.update(overrides)
    response = client.post("/equipment", json=payload)
    assert response.status_code == 201
    return response.get_json()


def create_renter(client, name="Sam", email="sam@example.com"):
    response = client.post("/renters", json={"name": name, "email": email})
    assert response.status_code == 201
    return response.get_json()


# ------------------------------------------------------------
# Features 1-3: add, list, and view equipment
# ------------------------------------------------------------


def test_create_equipment_returns_fields_and_persists(client):
    """A new item starts fully available, and a later GET returns the same data."""
    response = client.post("/equipment", json={
        "name": "Mountain Bike", "category": "Cycling", "total_units": 4,
    })
    assert response.status_code == 201
    item = response.get_json()
    assert item["name"] == "Mountain Bike"
    assert item["category"] == "Cycling"
    assert item["total_units"] == 4
    assert item["available_units"] == 4
    assert item["is_available"] is True

    fetched = client.get(f"/equipment/{item['id']}")
    assert fetched.status_code == 200
    assert fetched.get_json() == item


def test_create_equipment_defaults_to_one_unit(client):
    """Leaving out total_units creates a single unit that is available."""
    response = client.post("/equipment", json={"name": "Helmet", "category": "Safety"})
    assert response.status_code == 201
    item = response.get_json()
    assert item["total_units"] == 1
    assert item["available_units"] == 1


def test_list_equipment_returns_every_item_with_unique_ids(client):
    """The list holds every created item, in creation order, each with its own ID."""
    names = ["Kayak", "Canoe", "Paddle"]
    for name in names:
        create_equipment(client, name=name)

    listed = client.get("/equipment").get_json()
    assert [item["name"] for item in listed] == names
    assert len({item["id"] for item in listed}) == len(names)


def test_get_nonexistent_equipment_returns_404(client):
    """Looking up an ID that was never created gives a clear 'not found' error."""
    create_equipment(client)
    response = client.get("/equipment/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


def test_create_equipment_with_negative_units_is_rejected(client):
    """DEFECT (R1): stock counts must be meaningful, so a negative total is refused.

    Observed: the item is created with total_units = -2 and available_units = -2.
    """
    response = client.post("/equipment", json={
        "name": "Tent", "category": "Camping", "total_units": -2,
    })
    assert response.status_code == 400
    assert client.get("/equipment").get_json() == []


def test_create_equipment_missing_category_is_rejected(client):
    """DEFECT (R1): a request missing a required field gets a 400 error, not a crash.

    Observed: the route reads data["category"] directly and raises KeyError,
    which the running app reports as a 500 Internal Server Error.
    """
    response = client.post("/equipment", json={"name": "Tent"})
    assert response.status_code == 400


# ------------------------------------------------------------
# Features 4-5: update and delete equipment
# ------------------------------------------------------------


def test_update_equipment_persists_changes_and_keeps_other_fields(client):
    """Fields sent in a PUT are saved; fields left out keep their old values."""
    item = create_equipment(client, name="Kayak", category="Water", total_units=3)

    response = client.put(f"/equipment/{item['id']}", json={
        "name": "Sea Kayak", "total_units": 5,
    })
    assert response.status_code == 200

    fetched = client.get(f"/equipment/{item['id']}").get_json()
    assert fetched["name"] == "Sea Kayak"
    assert fetched["total_units"] == 5
    assert fetched["category"] == "Water"
    assert fetched["available_units"] == 3


def test_update_nonexistent_equipment_returns_404(client):
    """Updating an ID that does not exist fails and creates nothing."""
    response = client.put("/equipment/999", json={"name": "Ghost"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}
    assert client.get("/equipment").get_json() == []


def test_update_cannot_make_available_units_exceed_total(client):
    """DEFECT (R1): the shop cannot have more units on the shelf than it owns.

    Observed: setting available_units to 10 on an item with 2 total units is
    accepted, so the stock list reports 10 of 2 available.
    """
    item = create_equipment(client, total_units=2)
    response = client.put(f"/equipment/{item['id']}", json={"available_units": 10})
    assert response.status_code == 400
    assert client.get(f"/equipment/{item['id']}").get_json()["available_units"] == 2


def test_delete_equipment_removes_it_everywhere(client):
    """After a delete, the item is gone from lookup, availability and the list."""
    kept = create_equipment(client, name="Canoe")
    deleted = create_equipment(client, name="Paddle")

    response = client.delete(f"/equipment/{deleted['id']}")
    assert response.status_code == 204

    assert client.get(f"/equipment/{deleted['id']}").status_code == 404
    assert client.get(f"/equipment/{deleted['id']}/availability").status_code == 404
    assert [item["id"] for item in client.get("/equipment").get_json()] == [kept["id"]]


def test_delete_equipment_twice_returns_404(client):
    """Deleting an item that was already deleted reports it as not found."""
    item = create_equipment(client)
    assert client.delete(f"/equipment/{item['id']}").status_code == 204

    response = client.delete(f"/equipment/{item['id']}")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


# ------------------------------------------------------------
# Features 6-7: mark in/out of service and check availability
# ------------------------------------------------------------


def test_mark_out_of_service_shows_in_item_and_availability(client):
    """Taking an item out of service is visible everywhere; unit counts don't change."""
    item = create_equipment(client, total_units=2)

    response = client.patch(f"/equipment/{item['id']}/status", json={"is_available": False})
    assert response.status_code == 200
    assert response.get_json()["is_available"] is False

    assert client.get(f"/equipment/{item['id']}").get_json()["is_available"] is False
    availability = client.get(f"/equipment/{item['id']}/availability").get_json()
    assert availability == {
        "equipment_id": item["id"],
        "is_available": False,
        "available_units": 2,
        "total_units": 2,
    }


def test_out_of_service_item_can_be_put_back_in_service(client):
    """An item marked out of service can be marked available again."""
    item = create_equipment(client)
    client.patch(f"/equipment/{item['id']}/status", json={"is_available": False})

    response = client.patch(f"/equipment/{item['id']}/status", json={"is_available": True})
    assert response.status_code == 200
    assert client.get(f"/equipment/{item['id']}/availability").get_json()["is_available"] is True


def test_status_and_availability_of_nonexistent_equipment_return_404(client):
    """Both service-status endpoints report unknown IDs as not found."""
    status_response = client.patch("/equipment/999/status", json={"is_available": False})
    assert status_response.status_code == 404
    assert status_response.get_json() == {"error": "Equipment not found"}

    availability_response = client.get("/equipment/999/availability")
    assert availability_response.status_code == 404
    assert availability_response.get_json() == {"error": "Equipment not found"}


def test_availability_tracks_checkouts_and_returns(client):
    """Workflow: check out 2 of 3 units, then return one; availability follows each step."""
    item = create_equipment(client, total_units=3)
    renter = create_renter(client)

    rental_ids = []
    for _ in range(2):
        response = client.post("/rentals", json={"equipment_id": item["id"], "renter_id": renter["id"]})
        rental_ids.append(response.get_json()["id"])
    assert client.get(f"/equipment/{item['id']}/availability").get_json()["available_units"] == 1

    client.put(f"/rentals/{rental_ids[0]}/return")
    availability = client.get(f"/equipment/{item['id']}/availability").get_json()
    assert availability["available_units"] == 2
    assert availability["total_units"] == 3


def test_status_rejects_values_other_than_true_or_false(client):
    """DEFECT (R10): a damaged/out-of-service tag must be a clear yes/no value.

    Observed: sending "damaged" is accepted and stored as the string "damaged",
    so the item's is_available field is no longer true or false.
    """
    item = create_equipment(client)
    response = client.patch(f"/equipment/{item['id']}/status", json={"is_available": "damaged"})
    assert response.status_code == 400
    assert client.get(f"/equipment/{item['id']}").get_json()["is_available"] is True
