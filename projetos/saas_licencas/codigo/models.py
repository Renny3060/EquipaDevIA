from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    licenses = relationship("License", back_populates="client")


class License(Base):
    __tablename__ = 'licenses'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    license_key = Column(String(32), unique=True, index=True)
    status = Column(String(10), default='ACTIVE')
    expires_at = Column(DateTime)

    client = relationship("Client", back_populates="licenses")