from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from crud import create_license, revoke_license_key, validate_license_key
from schemas import (
    LicenseKeyRequest,
    LicenseRevocationRequest,
    LicenseValidateRequest,
    LicenseValidationResponse,
)

# Cria as tabelas na base de dados automaticamente ao arrancar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Gestão de Licenças")


@app.post("/api/licenses")
async def generate_license(
    license_key_request: LicenseKeyRequest, db: Session = Depends(get_db)
):
    created_license = create_license(
        db=db, license_key_request=license_key_request
    )
    return {
        "id": created_license.id,
        "client_id": created_license.client_id,
        "license_key": created_license.license_key,
        "status": created_license.status,
        "expires_at": created_license.expires_at,
    }


@app.post("/api/validate")
async def validate_license(
    validate_request: LicenseValidateRequest, db: Session = Depends(get_db)
):
    validation_response = validate_license_key(
        db=db, validate_request=validate_request
    )
    return {
        "valid": validation_response.valid,
        "reason": validation_response.reason,
        "expires_in_days": validation_response.expires_in_days,
    }


@app.post("/api/revoke")
async def revoke_license(
    license_revocation_request: LicenseRevocationRequest,
    db: Session = Depends(get_db),
):
    revoke_license_key(
        db=db, license_revocation_request=license_revocation_request
    )
    return {"message": "License revoked successfully"}