import unittest
from app.schemas import LicenseKeyRequest, LicenseValidationResponse, LicenseRevocationRequest

class TestSchemas(unittest.TestCase):
    def test_license_key_request_schema(self):
        request = LicenseKeyRequest(email="test@example.com", days_validity=30)
        
        self.assertEqual(request.email, "test@example.com")
        self.assertEqual(request.days_validity, 30)

    def test_license_validation_response_schema(self):
        response_active = LicenseValidationResponse(valid=True, expires_in_days=29)
        response_expired = LicenseValidationResponse(valid=False, reason="Expired")
        response_revoked = LicenseValidationResponse(valid=False, reason="Revoked")
        
        self.assertTrue(response_active.valid)
        self.assertIsNone(response_expired.reason)
        self.assertIsNone(response_revoked.reason)

    def test_license_revocation_request_schema(self):
        request = LicenseRevocationRequest(license_key="XXXX-XXXX-XXXX-XXXX")
        
        self.assertEqual(request.license_key, "XXXX-XXXX-XXXX-XXXX")

if __name__ == '__main__':
    unittest.main()
