import requests
from datetime import datetime
from sqlalchemy.orm import Session
from models.customer import Customer
import logging

logger = logging.getLogger(__name__)

FLASK_API_URL = "http://mock-server:5000/api/customers"

class IngestionService:
    """Service to ingest data from Flask API to PostgreSQL"""

    @staticmethod
    def fetch_all_customers_from_flask():
        """Fetch all customers from Flask API with pagination"""
        all_customers = []
        page = 1
        limit = 10

        try:
            while True:
                response = requests.get(
                    FLASK_API_URL,
                    params={'page': page, 'limit': limit},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                customers = data.get('data', [])
                if not customers:
                    break

                all_customers.extend(customers)
                
                total = data.get('total', 0)
                if len(all_customers) >= total:
                    break

                page += 1

            logger.info(f"Fetched {len(all_customers)} customers from Flask API")
            return all_customers

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Flask API: {str(e)}")
            raise

    @staticmethod
    def parse_date(date_string):
        """Parse date string to datetime object"""
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00')).date()
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def parse_datetime(datetime_string):
        """Parse datetime string to datetime object"""
        if not datetime_string:
            return None
        try:
            return datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def upsert_customers(db: Session, customers: list):
        """Upsert customers into database (update if exists, insert if new)"""
        try:
            records_processed = 0

            for customer_data in customers:
                customer_id = customer_data.get('customer_id')
                
                # Check if customer exists
                existing_customer = db.query(Customer).filter(
                    Customer.customer_id == customer_id
                ).first()

                # Parse date fields
                dob = IngestionService.parse_date(customer_data.get('date_of_birth'))
                created_at = IngestionService.parse_datetime(customer_data.get('created_at'))

                if existing_customer:
                    # Update existing customer
                    existing_customer.first_name = customer_data.get('first_name')
                    existing_customer.last_name = customer_data.get('last_name')
                    existing_customer.email = customer_data.get('email')
                    existing_customer.phone = customer_data.get('phone')
                    existing_customer.address = customer_data.get('address')
                    existing_customer.date_of_birth = dob
                    existing_customer.account_balance = customer_data.get('account_balance')
                    if created_at:
                        existing_customer.created_at = created_at
                else:
                    # Insert new customer
                    new_customer = Customer(
                        customer_id=customer_id,
                        first_name=customer_data.get('first_name'),
                        last_name=customer_data.get('last_name'),
                        email=customer_data.get('email'),
                        phone=customer_data.get('phone'),
                        address=customer_data.get('address'),
                        date_of_birth=dob,
                        account_balance=customer_data.get('account_balance'),
                        created_at=created_at
                    )
                    db.add(new_customer)

                records_processed += 1

            # Commit all changes
            db.commit()
            logger.info(f"Successfully upserted {records_processed} customers")
            return records_processed

        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting customers: {str(e)}")
            raise

    @staticmethod
    def ingest():
        """Main ingestion function: fetch from Flask and upsert to database"""
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # Fetch customers from Flask API
            customers = IngestionService.fetch_all_customers_from_flask()
            
            # Upsert to database
            records_processed = IngestionService.upsert_customers(db, customers)
            
            return {
                'status': 'success',
                'records_processed': records_processed
            }
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            db.close()
