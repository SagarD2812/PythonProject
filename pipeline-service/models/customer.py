from sqlalchemy import Column, String, Numeric, Date, DateTime
from database import Base
from datetime import datetime

class Customer(Base):
    """SQLAlchemy model for Customer"""
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    account_balance = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Customer(customer_id={self.customer_id}, first_name={self.first_name}, last_name={self.last_name})>"
