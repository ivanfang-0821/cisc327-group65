# ============================================================
# Ivan Fang: Assignment 3 tests
# ============================================================
# Coverage-directed tests for app/routes/views.py (the web UI pages).
# Baseline coverage of views.py was 47%: home, equipment_page,
# delete_equipment_page, renters_page, delete_renter_page, rentals_page
# and return_rental_page were largely untested.
#
# Every test checks behavior (page content, redirect target, or the data
# left in the store), not just the HTTP status code.

from datetime import date

from app import store


def add_equipment(client, name="Kayak", category="Boat", units=2):
    """Create equipment through the web form and return its id."""
    client.post(
        "/ui/equipment",
        data={"name": name, "category": category, "total_units": str(units)},
    )
    return max(store.equipment)


def add_renter(client, name="Sam", email="sam@example.com"):
    """Create a renter through the web form and return its id."""
    client.post("/ui/renters", data={"name": name, "email": email})
    return max(store.renters)


# ---------------- Home page ----------------

def test_home_page_shows_title_and_navigation(client):
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Equipment Rental Management" in html
    assert "Manage Equipment" in html
    assert "Manage Renters" in html
    assert "Manage Rentals" in html


# ---------------- Equipment page ----------------

def test_equipment_page_lists_existing_equipment(client):
    add_equipment(client, name="Canoe", category="Boat", units=3)

    response = client.get("/ui/equipment")

    assert response.status_code == 200
    assert "Canoe" in response.get_data(as_text=True)


def test_equipment_form_creates_item_with_all_units_available(client):
    response = client.post(
        "/ui/equipment",
        data={"name": "Tent", "category": "Camping", "total_units": "4"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/equipment")
    item = store.equipment[1]
    assert item.name == "Tent"
    assert item.category == "Camping"
    assert item.total_units == 4
    assert item.available_units == 4


def test_equipment_form_with_non_numeric_units_creates_nothing(client):
    # Boundary/error case: units must be a whole number.
    try:
        response = client.post(
            "/ui/equipment",
            data={"name": "Tent", "category": "Camping", "total_units": "abc"},
        )
        assert response.status_code >= 400
    except ValueError:
        pass  # the app lets the bad value raise; either way no item is saved
    assert store.equipment == {}


def test_delete_equipment_page_removes_item(client):
    equipment_id = add_equipment(client)

    response = client.post(f"/ui/equipment/{equipment_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/equipment")
    assert equipment_id not in store.equipment


def test_delete_equipment_page_unknown_id_changes_nothing(client):
    equipment_id = add_equipment(client)

    response = client.post("/ui/equipment/999/delete")

    assert response.status_code == 302
    assert list(store.equipment) == [equipment_id]


# ---------------- Renters page ----------------

def test_renters_page_lists_existing_renters(client):
    add_renter(client, name="Alex", email="alex@example.com")

    response = client.get("/ui/renters")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Alex" in html
    assert "alex@example.com" in html


def test_renters_form_creates_renter(client):
    response = client.post(
        "/ui/renters", data={"name": "Jo", "email": "jo@example.com"}
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/renters")
    renter = store.renters[1]
    assert renter.name == "Jo"
    assert renter.email == "jo@example.com"


def test_delete_renter_page_removes_renter(client):
    renter_id = add_renter(client)

    response = client.post(f"/ui/renters/{renter_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/renters")
    assert renter_id not in store.renters


def test_delete_renter_page_unknown_id_changes_nothing(client):
    renter_id = add_renter(client)

    response = client.post("/ui/renters/999/delete")

    assert response.status_code == 302
    assert list(store.renters) == [renter_id]


# ---------------- Rentals page: checkout ----------------

def test_rentals_page_lists_existing_rentals(client):
    equipment_id = add_equipment(client)
    renter_id = add_renter(client)
    client.post(
        "/ui/rentals",
        data={"equipment_id": str(equipment_id), "renter_id": str(renter_id)},
    )

    response = client.get("/ui/rentals")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Return" in html  # an unreturned rental offers a Return button


def test_rentals_form_checks_out_equipment(client):
    equipment_id = add_equipment(client, units=2)
    renter_id = add_renter(client)

    response = client.post(
        "/ui/rentals",
        data={"equipment_id": str(equipment_id), "renter_id": str(renter_id)},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/rentals")
    rental = store.rentals[1]
    assert rental.equipment_id == equipment_id
    assert rental.renter_id == renter_id
    assert rental.return_date is None
    assert store.equipment[equipment_id].available_units == 1


def test_rentals_form_refuses_unknown_equipment(client):
    renter_id = add_renter(client)

    response = client.post(
        "/ui/rentals", data={"equipment_id": "999", "renter_id": str(renter_id)}
    )

    assert response.status_code == 302
    assert store.rentals == {}


def test_rentals_form_refuses_when_no_units_left(client):
    equipment_id = add_equipment(client, units=1)
    renter_id = add_renter(client)
    data = {"equipment_id": str(equipment_id), "renter_id": str(renter_id)}
    client.post("/ui/rentals", data=data)

    client.post("/ui/rentals", data=data)  # second request: nothing left

    assert len(store.rentals) == 1
    assert store.equipment[equipment_id].available_units == 0


def test_rentals_form_refuses_out_of_service_equipment(client):
    equipment_id = add_equipment(client, units=2)
    renter_id = add_renter(client)
    store.equipment[equipment_id].is_available = False

    client.post(
        "/ui/rentals",
        data={"equipment_id": str(equipment_id), "renter_id": str(renter_id)},
    )

    assert store.rentals == {}
    assert store.equipment[equipment_id].available_units == 2


# ---------------- Rentals page: return ----------------

def test_return_rental_page_marks_returned_and_restores_unit(client):
    equipment_id = add_equipment(client, units=2)
    renter_id = add_renter(client)
    client.post(
        "/ui/rentals",
        data={"equipment_id": str(equipment_id), "renter_id": str(renter_id)},
    )

    response = client.post("/ui/rentals/1/return")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/rentals")
    assert store.rentals[1].return_date == date.today()
    assert store.equipment[equipment_id].available_units == 2


def test_return_rental_page_twice_does_not_add_a_second_unit(client):
    equipment_id = add_equipment(client, units=2)
    renter_id = add_renter(client)
    client.post(
        "/ui/rentals",
        data={"equipment_id": str(equipment_id), "renter_id": str(renter_id)},
    )
    client.post("/ui/rentals/1/return")

    client.post("/ui/rentals/1/return")

    assert store.equipment[equipment_id].available_units == 2


def test_return_rental_page_unknown_rental_changes_nothing(client):
    equipment_id = add_equipment(client, units=2)

    response = client.post("/ui/rentals/999/return")

    assert response.status_code == 302
    assert store.rentals == {}
    assert store.equipment[equipment_id].available_units == 2
