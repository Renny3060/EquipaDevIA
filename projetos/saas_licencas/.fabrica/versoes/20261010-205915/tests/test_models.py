import pytest
from app.models import Client, License

def test_client_model():
    client = Client(email="test@example.com")
    
    assert client.email == "test@example.com"
    assert isinstance(client.created_at, datetime)

def test_license_model():
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    expires_at = datetime.utcnow() + timedelta(days=license_key_request.days_validity)
    license = License(
        client_id=1,
        license_key="XXXX-XXXX-XXXX-XXXX",
        status='ACTIVE',
        expires_at=expires_at
    )
    
    assert license.client_id == 1
    assert license.license_key == "XXXX-XXXX-XXXX-XXXX"
    assert license.status == 'ACTIVE'
    assert license.expires_at == expires_at
