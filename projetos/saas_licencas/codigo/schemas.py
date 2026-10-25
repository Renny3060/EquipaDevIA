from pydantic import BaseModel, EmailStr, conint


class LicenseKeyRequest(BaseModel):
    email: EmailStr
    days_validity: conint(gt=0)


class LicenseValidateRequest(BaseModel):
    license_key: str


class LicenseValidationResponse(BaseModel):
    valid: bool
    reason: str = None
    expires_in_days: int = None


class LicenseRevocationRequest(BaseModel):
    license_key: str