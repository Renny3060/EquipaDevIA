import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Client, License
from schemas import (
    LicenseKeyRequest,
    LicenseRevocationRequest,
    LicenseValidateRequest,
    LicenseValidationResponse,
)


def generate_license_key():
    return '-'.join([uuid.uuid4().hex[:4] for _ in range(4)])


def get_client_by_email(db: Session, email: str):
    return db.query(Client).filter(Client.email == email).first()


def create_license(db: Session, license_key_request: LicenseKeyRequest):
    client = get_client_by_email(db, license_key_request.email)
    if not client:
        client = Client(email=license_key_request.email)
        db.add(client)
        db.commit()
        db.refresh(client)

    license_key = generate_license_key()
    expires_at = datetime.utcnow() + timedelta(days=license_key_request.days_validity)
    new_license = License(
        client_id=client.id,
        license_key=license_key,
        status='ACTIVE',
        expires_at=expires_at,
    )
    db.add(new_license)
    db.commit()
    db.refresh(new_license)

    return new_license


def validate_license_key(
    db: Session, validate_request: LicenseValidateRequest
) -> LicenseValidationResponse:
    license = (
        db.query(License)
        .filter(License.license_key == validate_request.license_key)
        .first()
    )

    if not license:
        return LicenseValidationResponse(valid=False, reason="Not Found")

    if license.status == 'REVOKED':
        return LicenseValidationResponse(valid=False, reason="Revoked")

    if datetime.utcnow() > license.expires_at:
        license.status = 'EXPIRED'
        db.commit()
        return LicenseValidationResponse(valid=False, reason="Expired")

    expires_in_days = (license.expires_at - datetime.utcnow()).days
    return LicenseValidationResponse(
        valid=True, expires_in_days=expires_in_days
    )


def revoke_license_key(
    db: Session, license_revocation_request: LicenseRevocationRequest
):
    license = (
        db.query(License)
        .filter(
            License.license_key == license_revocation_request.license_key
        )
        .first()
    )
    if license:
        license.status = 'REVOKED'
        db.commit()