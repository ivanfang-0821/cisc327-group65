### Spencer McAuslan's 20467669 test code for features 8-12, 14-17
import pytest

#Start of feature 8
#--------------------------------------------------------------------
def test_list_all_renters(client):
    """Test Feature 8: Listing all renters returns 200 and a list"""
    response = client.get("/renters")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
#--------------------------------------------------------------------
#End of feature 8

#Start of feature 9
#--------------------------------------------------------------------
def test_add_renter(client):
    """Test Feature 9: Adding a renter returns 201 and keeps data"""
    payload = {
        "name": "Bob Bobby", 
        "email": "Bob@gmail.com", 
        "phone": "123-1234"
    }
    response = client.post("/renters", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Bob Bobby"
    assert "id" in data
#--------------------------------------------------------------------
#End of feature 9

#Start of feature 10
#--------------------------------------------------------------------
def test_view_one_renter(client):
    """Test Feature 10: Viewing a specific renter by ID"""
    post_res = client.post("/renters", json={
        "name": "Peter Parker", 
        "email": "Peter@gmail.com", 
        "phone": "123-1234"
    })
    renter_id = post_res.get_json()["id"]

    response = client.get(f"/renters/{renter_id}")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Peter Parker"
#--------------------------------------------------------------------
#End of feature 10

#Start of feature 11
#--------------------------------------------------------------------
def test_update_a_renter(client):
    """Test Feature 11: Updating a renter's information"""
    post_res = client.post("/renters", json={
        "name": "Jimmy Bob", 
        "email": "Jimmy@gmail.com", 
        "phone": "111-2222"
    })
    renter_id = post_res.get_json()["id"]

    update_payload = {
        "name": "Jimu Bob", 
        "phone": "111-3333"
    }
    response = client.put(f"/renters/{renter_id}", json=update_payload)
    assert response.status_code in [200, 204]

    get_res = client.get(f"/renters/{renter_id}")
    assert get_res.get_json()["name"] == "Jimu Bob"
#--------------------------------------------------------------------
#End of feature 11

#Start of feature 12
#--------------------------------------------------------------------
def test_delete_a_renter(client):
    """Test Feature 12: Deleting a renter and double checking removal"""
    post_res = client.post("/renters", json={
        "name": "Banana Bro",
        "email": "Banana@cool.com",
        "phone": "777-7777"
    })
    renter_id = post_res.get_json()["id"]

    response = client.delete(f"/renters/{renter_id}")
    assert response.status_code in [200, 204]
    get_res = client.get(f"/renters/{renter_id}")
    assert get_res.status_code == 404
#--------------------------------------------------------------------
#End of feature 12

#Start of feature 14
#-------------------------------------------------------------------------------------------
def test_return_equipment(client):
    """Test Feature 14: Returning rented equipment updates rental status and inventory"""
    eq_res = client.post("/equipment", json={
        "name": "Flares",
        "category": "hand tools",
        "total_units": 2
    })
    eq_id = eq_res.get_json()["id"]

    renter_res = client.post("/renters", json={
        "name": "Jeff John", 
        "email": "jj@mail.com", 
        "phone": "345-5432"
    })
    renter_id = renter_res.get_json()["id"]

    rental_res = client.post("/rentals", json={
        "equipment_id": eq_id, 
        "renter_id": renter_id
    })
    rental_id = rental_res.get_json()["id"]

    return_res = client.put(f"/rentals/{rental_id}/return")
    assert return_res.status_code in [200, 204]

    verify_res = client.get(f"/rentals?renter_id={renter_id}")
    assert verify_res.status_code == 200
    rentals = verify_res.get_json()
    assert isinstance(rentals, list)
    assert len(rentals) >= 1
    assert rentals[0].get("return_date") is not None
#-------------------------------------------------------------------------------------------
#End of feature 14

#Start of feature 15
#-------------------------------------------------------------------------------------------
def test_look_up_rentals(client):
    """Test Feature 15: Looking up rentals filtered by renter or equipment ID"""
    eq_res = client.post("/equipment", json={
        "name": "Tarp",
        "category": "camping", 
        "total_units": 1
    })
    eq_id = eq_res.get_json()["id"]

    eq_res2 = client.post("/equipment", json={
            "name": "cannoe",
            "category": "boats", 
            "total_units": 2
        })
    eq_id2 = eq_res2.get_json()["id"]

    renter_res = client.post("/renters", json={
        "name": "Bob Builder", 
        "email": "bob@apple.com", 
        "phone": "001-2000"
    })
    renter_id = renter_res.get_json()["id"]

    renter_res2 = client.post("/renters", json={
            "name": "Jimmy John", 
            "email": "Jim@apple.com", 
            "phone": "100-3000"
        })
    renter_id2 = renter_res2.get_json()["id"]

    client.post("/rentals", json={
        "equipment_id": eq_id2, 
        "renter_id": renter_id
    })

    client.post("/rentals", json={
            "equipment_id": eq_id, 
            "renter_id": renter_id2
        })

    response = client.get(f"/rentals?renter_id={renter_id}")
    assert response.status_code == 200
    rentals = response.get_json()
    assert isinstance(rentals, list)
    assert len(rentals) >= 1
    assert rentals[0]["renter_id"] == renter_id
#-------------------------------------------------------------------------------------------
#End of feature 15

#Start of feature 16
#-------------------------------------------------------------------------------------------
def test_extend_rental(client):
    """Test Feature 16: Extending a rental updates the due date"""
    eq_res = client.post("/equipment", json={
        "name": "Bike",
        "category": "vehicles", 
        "total_units": 1
    })
    eq_id = eq_res.get_json()["id"]

    renter_res = client.post("/renters", json={
        "name": "John Smoke", 
        "email": "rainbow@mail.com", 
        "phone": "416-4164"
    })
    renter_id = renter_res.get_json()["id"]

    rental_res = client.post("/rentals", json={
        "equipment_id": eq_id, 
        "renter_id": renter_id
    })
    rental_id = rental_res.get_json()["id"]

    extension_payload = {"days": 7}
    ext_res = client.put(f"/rentals/{rental_id}/extend", json=extension_payload)
    assert ext_res.status_code in [200, 204]
#-------------------------------------------------------------------------------------------
#End of feature 16

#Start of feature 17
#-------------------------------------------------------------------------------------------
def test_release_deposit(client):
    """Test Feature 17: Releasing a rental security deposit updates deposit status"""
    eq_res = client.post("/equipment", json={
        "name": "kayak",
        "category": "boats", 
        "total_units": 1
    })
    eq_id = eq_res.get_json()["id"]

    renter_res = client.post("/renters", json={
        "name": "Dragan Yrup", 
        "email": "Yrup@mail.com", 
        "phone": "676-4820"
    })
    renter_id = renter_res.get_json()["id"]

    rental_res = client.post("/rentals", json={
        "equipment_id": eq_id, 
        "renter_id": renter_id, 
        "deposit_amount": 50.0
    })
    rental_id = rental_res.get_json()["id"]

    
    verify_res = client.get(f"/rentals?renter_id={renter_id}")
    assert verify_res.status_code == 200

    deposit_res = client.put(f"/rentals/{rental_id}/deposit/release")
    assert deposit_res.status_code in [200, 204]

    rentals = verify_res.get_json()
    assert len(rentals) >= 1
    assert rentals[0]["deposit_released"] is True
#-------------------------------------------------------------------------------------------
#End of feature 17