from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from crud import create_license, validate_license_key, revoke_license_key
from schemas import LicenseKeyRequest, LicenseValidationResponse, LicenseRevocationRequest

app = FastAPI()

@app.post("/api/licenses", response_model=LicenseValidationResponse)
def generate_license(license_key_request: LicenseKeyRequest, db: Session = Depends(get_db)):
    try:
        license = create_license(db, license_key_request)
        expires_in_days = (license.expires_at - datetime.utcnow()).days
        return {"valid": True, "expires_in_days": expires_in_days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate", response_model=LicenseValidationResponse)
def validate_license(license_key_request: LicenseKeyRequest, db: Session = Depends(get_db)):
    try:
        return validate_license_key(db, license_key_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/revoke", response_model=None)
def revoke_license(license_revocation_request: LicenseRevocationRequest, db: Session = Depends(get_db)):
    try:
        revoke_license_key(db, license_revocation_request)
        return {"detail": "License revoked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
