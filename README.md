# eCommerce Order Processing Service

This project is a serverless data processing service built on Google Cloud Platform. It provides an HTTP API to accept and store eCommerce order data in BigQuery and is automatically deployed via a CI/CD pipeline.

## Features

*   **Serverless HTTP API:** Accepts `POST` requests to ingest order data and `GET` requests to retrieve the current state of all orders.
*   **Immutable Data Store:** All versions of order data are stored chronologically in BigQuery, ensuring no data is ever lost.
*   **Layered Data Views:** Multiple BigQuery views provide clean, purpose-built datasets for analysis (latest order status, first-order events, lifecycle metrics) without duplicating data.
*   **Automated CI/CD Deployment:** Pushing to the `main` branch automatically triggers a Cloud Build pipeline that lints the code and deploys the Cloud Function.
*   **Infrastructure as Code:** All database objects (tables, views) are defined in version-controlled SQL files.
*   **Data Visualization:** A Looker Studio dashboard provides business insights into the data.

## Tech Stack

*   **Backend:** Python 3.11
*   **Cloud Provider:** Google Cloud Platform (GCP)
*   **Compute:** Google Cloud Functions (2nd Gen)
*   **Data Warehouse:** Google BigQuery
*   **CI/CD:** Google Cloud Build
*   **Visualization:** Google Looker Studio

---

## Project Structure

The repository is organized to separate application code from database logic, which is a best practice for maintainability.

```
/
|-- sql/                 # SQL definitions for all database objects
|   |-- tables/
|   |   |-- orders_raw.sql
|   |-- views/
|       |-- first_order_events_v.sql
|       |-- latest_order_v.sql
|       |-- order_lifecycle_metrics_v.sql
|
|-- main.py              # Source code for the Python Cloud Function
|-- requirements.txt     # Dependencies
|-- cloudbuild.yaml      # CI/CD pipeline configuration for Cloud Build
|-- README.md            # This file
|-- .gitignore
```

---

## Setup & Deployment

This project is configured for automated deployment. After a one-time setup of the GCP environment, all subsequent deployments of the Cloud Function are handled by the CI/CD pipeline.

### 1. One-Time Manual Setup

These steps are required once to prepare the Google Cloud project.

1.  **Configure Local SDK:**
    Set your active project in the gcloud CLI:
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

2.  **Enable APIs:**
    Enable all necessary APIs for the project.
    ```bash
    gcloud services enable \
      cloudfunctions.googleapis.com \
      run.googleapis.com \
      bigquery.googleapis.com \
      cloudbuild.googleapis.com \
      artifactregistry.googleapis.com
    ```

3.  **Create BigQuery Resources:**
    Create the dataset and the initial `orders_raw` table from its DDL file.
    ```bash
    bq --location=US mk ecommerce_orders
    bq mk --table "$(cat sql/tables/orders_raw.sql)"
    ```
    Then, create the analytical views from their definition files.
    ```bash
    bq mk --use_legacy_sql=false --view "$(<sql/views/latest_order_v.sql)" ecommerce_orders.latest_order_v
    bq mk --use_legacy_sql=false --view "$(<sql/views/first_order_events_v.sql)" ecommerce_orders.first_order_events_v
    bq mk --use_legacy_sql=false --view "$(<sql/views/order_lifecycle_metrics_v.sql)" ecommerce_orders.order_lifecycle_metrics_v
    ```

4.  **Create CI/CD Service Account:**
    For security, the CI/CD pipeline uses a dedicated service account. Create it and grant it the necessary permissions.
    ```bash
    # Create the service account
    gcloud iam service-accounts create cloud-build-function-deployer \
      --display-name="Cloud Build Function Deployer"

    # Grant permissions
    # Note: Replace YOUR_PROJECT_ID and the service account email where needed.
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:cloud-build-function-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/cloudfunctions.developer"
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:cloud-build-function-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.admin"
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:cloud-build-function-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.admin"
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:cloud-build-function-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
    ```

### 2. Automated Deployment (CI/CD)

The CI/CD pipeline is defined in `cloudbuild.yaml` and is triggered by pushes to the `main` branch.

1.  **Connect Repository:** In the GCP Console, go to **Cloud Build > Triggers**, connect your Git repository, and create a new trigger.
2.  **Configure Trigger:**
    *   **Event:** Push to a branch
    *   **Branch:** `^main$`
    *   **Configuration:** Cloud Build configuration file (`cloudbuild.yaml`)
    *   **Advanced > Service Account:** Select the `cloud-build-function-deployer` service account you created above.
3.  **Push to Deploy:** With the trigger active, any `git push origin main` will now automatically:
    *   Lint the Python code with `flake8`.
    *   Deploy the Cloud Function if linting succeeds.

---

## API Usage

**Base URL:** The trigger URL provided after deployment.

### POST /
Ingests an array of order data.
*   **`curl` Example:**
    ```bash
    curl -X POST <YOUR_FUNCTION_URL> -H "Content-Type: application/json" -d '[{"order_id": "A1001", "order_date": "2025-08-08T10:00:00Z", "order_details": "Laptop, Mouse", "order_status": "Processing"}]'
    ```

### GET /
Retrieves the most recent entry for every unique order ID.
*   **`curl` Example:**
    ```bash
    curl <YOUR_FUNCTION_URL>
    ```

---

## Looker Studio Dashboard

A dashboard has been created for data visualization. It provides at-a-glance metrics on order statuses, performance, and trends.

**[Link to Looker Studio Dashboard]**