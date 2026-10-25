import unittest
from app.models import Client, License

class TestModels(unittest.TestCase):
    def test_client_model(self):
        client = Client(email="test@example.com")
        
        self.assertEqual(client.email, "test@example.com")
        self.assertIsInstance(client.created_at, datetime)

    def test_license_model(self):
        license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
        expires_at = datetime.utcnow() + timedelta(days=license_key_request.days_validity)
        license = License(
            client_id=1,
            license_key="XXXX-XXXX-XXXX-XXXX",
            status='ACTIVE',
            expires_at=expires_at
        )
        
        self.assertEqual(license.client_id, 1)
        self.assertEqual(license.license_key, "XXXX-XXXX-XXXX-XXXX")
        self.assertEqual(license.status, 'ACTIVE')
        self.assertEqual(license.expires_at, expires_at)

if __name__ == '__main__':
    unittest.main()
