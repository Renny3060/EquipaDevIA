import pytest
from app.schemas import LicenseKeyRequest, LicenseValidationResponse, LicenseRevocationRequest

def test_license_key_request_schema():
    request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    
    assert request.email == "test@example.com"
    assert request.days_validity == 30

def test_license_validation_response_schema():
    response_active = LicenseValidationResponse(valid=True, expires_in_days=29)
    response_expired = LicenseValidationResponse(valid=False, reason="Expired")
    response_revoked = LicenseValidationResponse(valid=False, reason="Revoked")
    
    assert response_active.valid
    assert not response_expired.reason
    assert not response_revoked.reason

def test_license_revocation_request_schema():
    request = LicenseRevocationRequest(license_key="XXXX-XXXX-XXXX-XXXX")
    
    assert request.license_key == "XXXX-XXXX-XXXX-XXXX"
