# eCommerce Order Processing Service

This project is a complete, serverless data processing service on Google Cloud Platform. It provides a public HTTP API, an immutable data backend in BigQuery, and a live Looker Studio dashboard. The entire infrastructure is defined as code and deployed automatically via a CI/CD pipeline.

## Live Demo & API Endpoint

[![Looker Studio](https://img.shields.io/badge/Live%20Dashboard-Looker%20Studio-blue?style=for-the-badge&logo=looker)](https://lookerstudio.google.com/s/ocd-REC5Quk)
[![API Endpoint](https://img.shields.io/badge/API%20Endpoint-Live-green?style=for-the-badge)](https://us-central1-orbit-test-project-468319.cloudfunctions.net/order-processor)

*   **Live Dashboard:** [https://lookerstudio.google.com/s/ocd-REC5Quk](https://lookerstudio.google.com/s/ocd-REC5Quk)
*   **API Function URL:** `https://us-central1-orbit-test-project-468319.cloudfunctions.net/order-processor`

### Quickstart API Testing

You can test the live API directly using `curl`.

**1. POST new order data:**
```bash
curl -X POST https://us-central1-orbit-test-project-468319.cloudfunctions.net/order-processor \
-H "Content-Type: application/json" \
-d '[{"order_id": "XYZ-999", "order_date": "2025-08-15T12:00:00Z", "order_details": "Test Item from README", "order_status": "Processing"}]'
```

**2. GET the latest state of all orders:**
```bash
curl https://us-central1-orbit-test-project-468319.cloudfunctions.net/order-processor
```

## Key Features

*   **Serverless HTTP API:** Accepts `POST` and `GET` requests via a Gen 2 Google Cloud Function.
*   **Immutable Data Store:** All order versions are stored chronologically in BigQuery, ensuring no data is ever lost.
*   **Layered Data Views:** Multiple BigQuery views provide clean, purpose-built datasets for analysis (latest status, first-order events, lifecycle metrics) without duplicating data.
*   **Automated CI/CD:** Pushing to the `main` branch automatically triggers a Cloud Build pipeline that lints and deploys the Cloud Function.
*   **Infrastructure as Code (IaC):** All database objects (tables, views) are defined in version-controlled SQL files.

## Tech Stack

*   **Backend:** Python 3.11
*   **Cloud Provider:** Google Cloud Platform (GCP)
*   **Compute:** Google Cloud Functions (2nd Gen)
*   **Data Warehouse:** Google BigQuery
*   **CI/CD:** Google Cloud Build
*   **Visualization:** Google Looker Studio

---

## Project Structure

The repository is organized to separate application code from database logic.

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

## Automated Deployment (CI/CD)

The primary deployment method for this project is through the automated CI/CD pipeline defined in `cloudbuild.yaml`.

*   **Trigger:** The pipeline runs on any `git push` to the `main` branch.
*   **Process:**
    1.  **Lint:** The Python code is linted with `flake8` to ensure code quality.
    2.  **Deploy:** If linting passes, Cloud Build deploys the function using the configuration in the YAML file.
*   **Identity:** The pipeline executes using a dedicated, user-managed service account (`cloud-build-function-deployer`) with the principle of least privilege in mind.

---

## Manual Setup & Replication

These steps are for the one-time setup of a new GCP project or for anyone wishing to replicate the environment from scratch.

### 1. Configure Local Environment
```bash
# Set your target project in the gcloud CLI
gcloud config set project YOUR_PROJECT_ID

# Enable all necessary APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 2. Create BigQuery Resources
Create the dataset, the `orders_raw` table from its DDL file, and all analytical views.
```bash
bq --location=US mk ecommerce_orders
bq mk --table "$(cat sql/tables/orders_raw.sql)"

# Create the analytical views
bq mk --use_legacy_sql=false --view "$(<sql/views/latest_order_v.sql)" ecommerce_orders.latest_order_v
bq mk --use_legacy_sql=false --view "$(<sql/views/first_order_events_v.sql)" ecommerce_orders.first_order_events_v
bq mk --use_legacy_sql=false --view "$(<sql/views/order_lifecycle_metrics_v.sql)" ecommerce_orders.order_lifecycle_metrics_v
```

### 3. Create and Configure CI/CD Service Account
This dedicated service account is used by the Cloud Build trigger for secure deployments.
```bash
# Create the service account
gcloud iam service-accounts create cloud-build-function-deployer \
  --display-name="Cloud Build Function Deployer"

# Grant it the necessary permissions
SA_EMAIL="cloud-build-function-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/cloudfunctions.developer"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/run.admin"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/iam.serviceAccountUser"
```

### 4. Connect Cloud Build Trigger
In the GCP Console, navigate to **Cloud Build > Triggers** to connect your repository and create a new trigger pointing to `cloudbuild.yaml` and using the service account created above.