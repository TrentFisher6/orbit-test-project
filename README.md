# eCommerce Order Processing Service

This project is a serverless data processing service built on Google Cloud Platform. It provides an HTTP API to accept and store eCommerce order data in BigQuery and retrieve the most current status for any given order. The solution includes a Google Cloud Function, a BigQuery data store with a view for real-time analysis, and a Looker Studio dashboard for visualization.

## Architecture Overview

The service follows a simple, scalable, serverless architecture:

```
+-----------+      HTTP POST/GET      +-----------------------+      +------------------+
|           |   ------------------>   |                       |      |                  |
|   User /  |                         |  Google Cloud Function|----->| BigQuery Table   |
| API Client|   <------------------   |      (Python)         |      | (orders_raw)     |
|           |     JSON Response       |                       |      |                  |
+-----------+                         +-----------------------+      +------------------+
                                                 |
                                                 | Queries
                                                 V
                                     +--------------------+
                                     |                    |
                                     |   BigQuery View    |
                                     | (latest_orders_v)  |
                                     |                    |
                                     +--------------------+
                                                 |
                                                 | Connects to
                                                 V
                                     +--------------------+
                                     |                    |
                                     |  Looker Studio     |
                                     |    Dashboard       |
                                     |                    |
                                     +--------------------+

```

## Features

*   **HTTP API:** Accepts `POST` requests to ingest new order data and `GET` requests to retrieve the latest state of all orders.
*   **Data Persistence:** All versions of order data are stored in a BigQuery table, ensuring no data is ever lost.
*   **Real-time View:** A BigQuery view provides a clean, up-to-the-minute look at the most recent entry for each unique order ID.
*   **Serverless & Scalable:** Built with Google Cloud Functions and BigQuery, the architecture automatically scales with request volume and data size.
*   **Data Visualization:** A Looker Studio dashboard provides business insights into the latest order data.

## Tech Stack

*   **Backend:** Python 3.11
*   **Cloud Provider:** Google Cloud Platform (GCP)
*   **Compute:** Google Cloud Functions (2nd Gen)
*   **Data Warehouse:** Google BigQuery
*   **Visualization:** Google Looker Studio
*   **Deployment:** Google Cloud CLI (`gcloud`)

---

## Setup and Deployment

Follow these steps to configure and deploy the service in your own Google Cloud project.

### Prerequisites

1.  An active Google Cloud Platform project.
2.  [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated on your local machine.
3.  Python 3.8+ installed locally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/TrentFisher6/orbit-test-project.git
cd orbit-test-project
```

### Step 2: Configure GCP Project

1.  Set your active project in the gcloud CLI:
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

2.  Enable the necessary APIs for the project.
    ```bash
    gcloud services enable \
      cloudfunctions.googleapis.com \
      run.googleapis.com \
      bigquery.googleapis.com \
      cloudbuild.googleapis.com \
      artifactregistry.googleapis.com
    ```

### Step 3: Create BigQuery Dataset and Table

1.  Create a BigQuery dataset to hold your resources.
    ```bash
    bq --location=US mk ecommerce_orders
    ```
2.  Create the `orders_raw` table with the correct schema. This table will store all incoming order events.
    ```bash
    bq mk --table ecommerce_orders.orders_raw \
    order_id:STRING,order_date:TIMESTAMP,order_details:STRING,order_status:STRING,ingestion_timestamp:TIMESTAMP
    ```

### Step 4: Create the BigQuery View

This view uses a window function to find the most recent record for each `order_id` based on `order_date`.

1.  Create a file named `view_query.sql` and add the following SQL. **Remember to replace `YOUR_PROJECT_ID`**.
    ```sql
    SELECT
      order_id,
      order_date,
      order_details,
      order_status
    FROM (
      SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY order_date DESC, ingestion_timestamp DESC) as rn
      FROM
        `YOUR_PROJECT_ID.ecommerce_orders.orders_raw`
    )
    WHERE
      rn = 1
    ```
2.  Create the view using the `bq` command.
    ```bash
    bq mk --use_legacy_sql=false --view "$(cat view_query.sql)" ecommerce_orders.latest_orders_v
    ```

### Step 5: Deploy the Cloud Function

Deploy the function using the `gcloud` CLI from the root of the project directory.

```bash
gcloud functions deploy order-processor \
  --gen2 \
  --runtime=python311 \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --source=. \
  --entry-point=handle_request \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID
```

Upon successful deployment, the command will output a trigger URL. This is your API endpoint.

### Environment Variables

The Cloud Function uses environment variables for configuration. You can set these during deployment or in the Google Cloud Console:

#### Required Environment Variables

- **`PROJECT_ID`**: Your Google Cloud Project ID (e.g., `"my-project-123456"`)
  - **Purpose**: Used for BigQuery table references and queries

#### Setting Environment Variables

**Option 1: During Deployment (Recommended)**
```bash
gcloud functions deploy order-processor \
  --gen2 \
  --runtime=python311 \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --source=. \
  --entry-point=handle_request \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID
```

**Option 2: Via Google Cloud Console**
1. Go to **Cloud Functions** in the Google Cloud Console
2. Select your function (`order-processor`)
3. Go to the **Edit** tab
4. Scroll down to **Environment variables**
5. Add:
   - **Variable name**: `PROJECT_ID`
   - **Value**: Your actual project ID
6. Click **Deploy** to save changes

**Option 3: Local Development**
For local testing, you can set environment variables before running:
```bash
export PROJECT_ID=your-actual-project-id
python -m functions-framework --target=handle_request --debug
```

---

## Usage (API Endpoints)

**Base URL:** The trigger URL provided after deployment.

### POST /

Ingests an array of order data into the system.

*   **Method:** `POST`
*   **Headers:** `Content-Type: application/json`
*   **Body:** A JSON array of order objects.

**`curl` Example:**
```bash
curl -X POST <YOUR_FUNCTION_URL> \
-H "Content-Type: application/json" \
-d '[
  {"order_id": "A1001", "order_date": "2025-08-08T10:00:00Z", "order_details": "Laptop, Mouse", "order_status": "Processing"},
  {"order_id": "B2002", "order_date": "2025-08-08T11:00:00Z", "order_details": "Keyboard", "order_status": "Shipped"},
  {"order_id": "A1001", "order_date": "2025-08-08T12:30:00Z", "order_details": "Laptop, Mouse", "order_status": "Shipped"}
]'
```
**Success Response (201 Created):**
```
Data successfully inserted.
```

### GET /

Retrieves the most recent entry for every unique order ID.

*   **Method:** `GET`

**`curl` Example:**
```bash
curl <YOUR_FUNCTION_URL>
```
**Success Response (200 OK):**
```json
[
  {
    "order_id": "B2002",
    "order_date": "2025-08-08T11:00:00Z",
    "order_details": "Keyboard",
    "order_status": "Shipped"
  },
  {
    "order_id": "A1001",
    "order_date": "2025-08-08T12:30:00Z",
    "order_details": "Laptop, Mouse",
    "order_status": "Shipped"
  }
]
```

## Looker Studio Dashboard

A dashboard has been created to visualize the data from the `latest_orders_v` view. It provides at-a-glance metrics on order statuses and trends.

**[Will insert a link here! -Trent]**

To recreate or build your own dashboard:
1.  Open Looker Studio and create a new data source.
2.  Select the **BigQuery** connector.
3.  Navigate to your project, the `ecommerce_orders` dataset, and select the `latest_orders_v` view.
4.  Build charts using the available fields.