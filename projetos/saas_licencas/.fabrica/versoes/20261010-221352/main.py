from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
import streamlit as st

from database import Base, engine, get_db
from crud import create_license, revoke_license_key, validate_license_key
from schemas import (
    LicenseKeyRequest,
    LicenseRevocationRequest,
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
    validate_request: LicenseKeyRequest, db: Session = Depends(get_db)
):
    validation_response = validate_license_key(
        db=db, license_key_request=validate_request
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

# Streamlit interface
def main():
    st.title("Sistema de Gestão de Licenças")

    # Dashboard metrics
    with st.container():
        st.header("Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_licenses = len(db.query(License).all())
            st.metric(label="Total de Licenças", value=total_licenses)
        with col2:
            active_licenses = len(db.query(License).filter_by(status='ACTIVE').all())
            st.metric(label="Licenças Ativas", value=active_licenses)
        with col3:
            revoked_or_expired_licenses = len(db.query(License).filter(License.status.in_(['REVOKED', 'EXPIRED'])).all())
            st.metric(label="Licenças Revogadas/Expiradas", value=revoked_or_expired_licenses)

    # License generation
    with st.container():
        st.header("Geração de Licença")
        email = st.text_input("Email do Cliente")
        days_validity = st.number_input("Validade em Dias", min_value=1, step=1)
        if st.button("Gerar Licença"):
            license_key_request = LicenseKeyRequest(email=email, days_validity=int(days_validity))
            response = create_license(db=get_db(), license_key_request=license_key_request)
            st.success(f"Licença gerada com sucesso! Chave: {response['license_key']}")

    # License validation
    with st.container():
        st.header("Validação de Licença")
        license_key = st.text_input("Chave da Licença")
        if st.button("Verificar Estado"):
            validate_request = LicenseKeyRequest(license_key=license_key)
            response = validate_license(db=get_db(), license_key_request=validate_request)
            if response['valid']:
                st.success(f"Licença VÁLIDA! Expira em {response['expires_in_days']} dias")
            elif response['reason'] == "Not Found":
                st.error("Licença NÃO ENCONTRADA!")
            else:
                st.error(f"Licença REVOGADA/EXPIRADA: {response['reason']}")

    # License revocation
    with st.container():
        st.header("Revogação de Licença")
        license_key = st.text_input("Chave da Licença para Revogar")
        if st.button("Revogar Licença"):
            revoke_request = LicenseKeyRequest(license_key=license_key)
            response = revoke_license(db=get_db(), license_revocation_request=revoke_request)
            st.success(response['message'])

if __name__ == "__main__":
    main()
