import functions_framework
from google.cloud import bigquery
from flask import jsonify
import datetime
import pytz

# Initialize the BigQuery client globally to reuse the connection
client = bigquery.Client()

# Define the project, dataset, and table details
PROJECT_ID = "orbit-test-project-468319"
DATASET_ID = "ecommerce_orders"
TABLE_ID = "orders_raw"
VIEW_ID = "latest_orders_v"

@functions_framework.http
def handle_request(req):
    """
    Main Cloud Function entry point.
    Routes requests to the appropriate handler based on the HTTP method.
    """
    if req.method == 'POST':
        return handle_post(req)
    elif req.method == 'GET':
        return handle_get(req)
    else:
        # Return a 405 Method Not Allowed error for other methods like PUT, DELETE
        return 'Method Not Allowed', 405

def handle_post(req):
    """Handles POST requests to insert order data into BigQuery."""
    try:
        orders = req.get_json()
        if not isinstance(orders, list):
            return 'Invalid payload format. Expected a JSON array.', 400
    except Exception as e:
        return f'Invalid JSON format: {e}', 400

    rows_to_insert = []
    errors = []

    # Get the current time in UTC for the ingestion timestamp
    ingestion_time = datetime.datetime.now(pytz.utc)

    for order in orders:
        # --- Data Validation ---
        if not isinstance(order, dict):
            errors.append("Invalid item in array: not a JSON object.")
            continue
        if not all(k in order for k in ['order_id', 'order_date', 'order_status']):
            errors.append(f"Missing required field in order: {order}")
            continue

        # --- Data Enrichment ---
        # Add the server-side ingestion timestamp
        order['ingestion_timestamp'] = ingestion_time.isoformat()
        rows_to_insert.append(order)

    if errors:
        # Return a detailed error message if any orders were invalid
        return jsonify({"success": False, "errors": errors}), 400

    if not rows_to_insert:
        return 'No valid order data to insert.', 400

    # --- Insert into BigQuery ---
    try:
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        table = client.get_table(table_ref)  # API request to get table schema
        insert_errors = client.insert_rows_json(table, rows_to_insert)

        if not insert_errors:
            return 'Data successfully inserted.', 201 # 201 Created is more appropriate
        else:
            return jsonify({"success": False, "errors": insert_errors}), 500

    except Exception as e:
        return f'An error occurred while inserting data into BigQuery: {e}', 500

def handle_get(req):
    """Handles GET requests to retrieve the latest entry for each order."""
    view_path = f"`{PROJECT_ID}.{DATASET_ID}.{VIEW_ID}`"
    query = f"SELECT * FROM {view_path}"

    try:
        # Execute the query
        query_job = client.query(query)

        # Wait for the job to complete and fetch the results
        results = query_job.result()

        # Convert the BigQuery Row objects into a list of dictionaries
        orders_list = [dict(row) for row in results]

        # Return the data as a JSON response
        return jsonify(orders_list), 200

    except Exception as e:
        return f'An error occurred while querying BigQuery: {e}', 500