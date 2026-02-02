from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

from database import init_db, get_db
from models.customer import Customer
from services.ingestion import IngestionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title="Customer Data Pipeline", version="1.0.0")

# Pydantic models for responses
class CustomerResponse(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    account_balance: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    data: List[CustomerResponse]
    total: int
    page: int
    limit: int

class IngestionResponse(BaseModel):
    status: str
    records_processed: int
    message: Optional[str] = None

@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pipeline-service"
    }

@app.post("/api/ingest", response_model=IngestionResponse, tags=["ingestion"])
async def ingest_data():
    """Ingest customer data from Flask API into PostgreSQL"""
    try:
        result = IngestionService.ingest()
        
        if result['status'] == 'success':
            return IngestionResponse(
                status="success",
                records_processed=result['records_processed']
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('message', 'Ingestion failed')
            )
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )

@app.get("/api/customers", response_model=PaginatedResponse, tags=["customers"])
async def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated list of customers from database"""
    try:
        # Get total count
        total = db.query(Customer).count()
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Query customers
        customers = db.query(Customer).order_by(
            desc(Customer.created_at)
        ).offset(skip).limit(limit).all()
        
        return PaginatedResponse(
            data=customers,
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["customers"])
async def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Get single customer by ID"""
    try:
        customer = db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found"
            )
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info("FastAPI pipeline service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown"""
    logger.info("FastAPI pipeline service shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
