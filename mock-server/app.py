from flask import Flask, jsonify, request
import json
import os
from pathlib import Path

app = Flask(__name__)
# //code from development branch1
# //code from development branch2
# //code from development branch
# Load customer data from JSON file
DATA_DIR = Path(__file__).parent / 'data'
CUSTOMERS_FILE = DATA_DIR / 'customers.json'

def load_customers():
    """Load customer data from JSON file"""
    try:
        with open(CUSTOMERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'mock-server'}), 200

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get paginated list of customers"""
    customers = load_customers()
    
    # Get pagination parameters
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10
    
    # Calculate pagination
    total = len(customers)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated_customers = customers[start_idx:end_idx]
    
    response = {
        'data': paginated_customers,
        'total': total,
        'page': page,
        'limit': limit
    }
    
    return jsonify(response), 200

@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get single customer by ID"""
    customers = load_customers()
    
    customer = next((c for c in customers if c['customer_id'] == customer_id), None)
    
    if not customer:
        return jsonify({'error': f'Customer {customer_id} not found'}), 404
    
    return jsonify({
        'data': customer,
        'total': 1,
        'page': 1,
        'limit': 1
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
