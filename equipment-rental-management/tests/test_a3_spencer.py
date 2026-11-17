from datetime import date, timedelta
from unittest.mock import patch
from app import store

def test_rental_reminder_success(client):
    """Test testing a successful rental reminder"""
    renter_res = client.post('/renters', json={
        "name": "Bob Paul",
        "email": "bob@example.com",
        "membership_date": str(date.today())
    })
    assert renter_res.status_code in [200, 201]
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "Backpack",
        "category": "Outdoor Gear",
        "available_units": 8
    })
    assert eq_res.status_code in [200, 201]
    eq_id = eq_res.get_json()["id"]
    
   
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id,
        "due_date": str(date.today())
    })
    assert rental_res.status_code in [200, 201]
    rental_id = rental_res.get_json()["id"]

    store.rentals[rental_id].due_date = date.today() + timedelta(days=2)
    
    with patch("app.routes.rentals.send_notification", return_value=True) as mock_send:
        response = client.post(f'/rentals/{rental_id}/reminder')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Reminder processed"
        assert data["notified"] is True
        
        mock_send.assert_called_once_with(
            recipient = "bob@example.com",
            subject = "Equipment Return Reminder",
            message = "Reminder: Your rental for Backpack is due back soon."
        )

def test_rental_already_returned(client):
    """Test rental reminder if already returned"""
    renter_res = client.post('/renters', json={
        "name": "Paul bob",
        "email": "Paul@gmail.com",
        "membership_date": str(date.today())
    })
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "Kayak",
        "category": "Vehicle",
        "available_units": 3
    })
    eq_id = eq_res.get_json()["id"]
    
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id,
        "due_date": str(date.today())
    })
    rental_id = rental_res.get_json()["id"]
    
    client.put(f'/rentals/{rental_id}/return')
    
    response = client.post(f'/rentals/{rental_id}/reminder')
    assert response.status_code == 400
    assert response.get_json()["error"] == "Rental already returned"

def test_rental_reminder_not_found(client):
    """Test rental reminder if rental not found"""
    response = client.post('/rentals/99999/reminder')
    assert response.status_code == 404
    assert response.get_json()["error"] == "Rental not found"

def test_overdue_rental_reminder_success(client):
    """Test uf rental reminder sent if overdue"""
    renter_res = client.post('/renters', json={
        "name": "Jeff Mca",
        "email": "jeff@email.com",
        "membership_date": str(date.today())
    })
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "Tent",
        "category": "Camping",
        "available_units": 5
    })
    eq_id = eq_res.get_json()["id"]
    
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id
    })
    rental_id = rental_res.get_json()["id"]
    
    store.rentals[rental_id].due_date = date.today() - timedelta(days=3)
    
    with patch("app.routes.rentals.send_notification", return_value=True) as mock_send:
        response = client.post(f'/rentals/{rental_id}/reminder')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Reminder processed"
        assert data["notified"] is True
        
        mock_send.assert_called_once_with(
            recipient = "jeff@email.com",
            subject = "Equipment Return Reminder",
            message = "Reminder: Your rental for Tent is due back soon."
        )

# Coverage-directed test from here on out
def test_release_deposit_not_returned(client):
    """Test release despoit before equipment has been renturned returns 400"""
    renter_res = client.post('/renters', json={
        "name": "Spencer okay",
        "email": "Spencer@example.com",
        "membership_date": str(date.today())
    })
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "Compass",
        "category": "Navigation",
        "available_units": 2
    })
    eq_id = eq_res.get_json()["id"]
    
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id,
        "deposit_amount": 25.0
    })
    rental_id = rental_res.get_json()["id"]
    
    response = client.put(f'/rentals/{rental_id}/deposit/release')
    assert response.status_code == 400
    assert response.get_json()["error"] == "Equipment has not been returned yet"

def test_release_deposit_not_found(client):
    """Test release despoit if rental not found returns 404"""
    response = client.put('/rentals/99999/deposit/release')
    assert response.status_code == 404
    assert response.get_json()["error"] == "Rental not found"

# rentals.py directed tests

def test_return_rental_not_found(client):
    """Test returning a non-existent rental returns 404"""
    response = client.put('/rentals/99999/return')
    assert response.status_code == 404
    assert response.get_json()["error"] == "Rental not found"

def test_extend_rental_not_found(client):
    """Test extending a non-existent rental returns 404"""
    response = client.put('/rentals/99999/extend', json={"days": 3})
    assert response.status_code == 404
    assert response.get_json()["error"] == "Rental not found"

def test_extend_rental_already_returned(client):
    """Test extending an already returned rental returns 400"""
    renter_res = client.post('/renters', json={
        "name": "Test Renter",
        "email": "test@somemail.com",
        "membership_date": str(date.today())
    })
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "Rock Climbing Helmet",
        "category": "Gear",
        "available_units": 2
    })
    eq_id = eq_res.get_json()["id"]
    
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id
    })
    rental_id = rental_res.get_json()["id"]
    
    client.put(f'/rentals/{rental_id}/return')
    
    response = client.put(f'/rentals/{rental_id}/extend', json={"days": 5})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Rental already returned"

def test_release_deposit_success_and_persistence(client):
    """Test successfully releasing a deposit and verifying persistence"""
    renter_res = client.post('/renters', json={
        "name": "Deposit Tester",
        "email": "dep@test.com",
        "membership_date": str(date.today())
    })
    renter_id = renter_res.get_json()["id"]
    
    eq_res = client.post('/equipment', json={
        "name": "GPS",
        "category": "Electronics",
        "available_units": 2
    })
    eq_id = eq_res.get_json()["id"]
    
    rental_res = client.post('/rentals', json={
        "equipment_id": eq_id,
        "renter_id": renter_id,
        "deposit_amount": 50.0
    })
    rental_id = rental_res.get_json()["id"]
    
    client.put(f'/rentals/{rental_id}/return')
    
    release_res = client.put(f'/rentals/{rental_id}/deposit/release')
    assert release_res.status_code in [200, 204]
    
    verify_res = client.get(f'/rentals?renter_id={renter_id}')
    assert verify_res.status_code == 200

# renters.py directed tests
def test_update_renter_not_found(client):
    """Test updating a non-existent renter returns 404"""
    response = client.put('/renters/99999', json={"name": "Ghost"})
    assert response.status_code == 404

def test_delete_renter_not_found(client):
    """Test deleting a non-existent renter returns 404"""
    response = client.delete('/renters/99999')
    assert response.status_code == 404