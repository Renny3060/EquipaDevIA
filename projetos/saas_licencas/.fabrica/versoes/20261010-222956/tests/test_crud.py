import pytest
from datetime import timedelta
from sqlalchemy.orm import Session
from database import get_db
from crud import create_license, validate_license_key, revoke_license_key
from app.models import LicenseKeyRequest, LicenseRevocationRequest

@pytest.fixture(scope="module")
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_create_license(db: Session):
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    created_license = create_license(db, license_key_request)
    
    assert created_license is not None
    assert created_license.client.email == "test@example.com"
    assert created_license.status == 'ACTIVE'
    assert (datetime.utcnow() + timedelta(days=29) < created_license.expires_at < datetime.utcnow() + timedelta(days=31))

def test_validate_active_license(db: Session):
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    create_license(db, license_key_request)
    
    validation_response = validate_license_key(db, LicenseKeyRequest(license_key=create_license.db.query(License).first().license_key))
    
    assert validation_response.valid
    assert not validation_response.reason

def test_validate_expired_license(db: Session):
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=1)
    create_license(db, license_key_request)
    
    db.query(License).update({"expires_at": datetime.utcnow() - timedelta(days=2)})
    db.commit()
    
    validation_response = validate_license_key(db, LicenseKeyRequest(license_key=create_license.db.query(License).first().license_key))
    
    assert not validation_response.valid
    assert validation_response.reason == "Expired"

def test_validate_revoked_license(db: Session):
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    create_license(db, license_key_request)
    
    revoke_license_key(db, LicenseRevocationRequest(license_key=create_license.db.query(License).first().license_key))
    
    validation_response = validate_license_key(db, LicenseKeyRequest(license_key=create_license.db.query(License).first().license_key))
    
    assert not validation_response.valid
    assert validation_response.reason == "Revoked"

def test_revoke_license(db: Session):
    license_key_request = LicenseKeyRequest(email="test@example.com", days_validity=30)
    create_license(db, license_key_request)
    
    revoke_license_key(db, LicenseRevocationRequest(license_key=create_license.db.query(License).first().license_key))
    
    revoked_license = db.query(License).filter_by(license_key=create_license.db.query(License).first().license_key).one()
    
    assert revoked_license.status == 'REVOKED'
