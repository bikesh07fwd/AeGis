# Service Account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "aegis-cloudrun-sa"
  display_name = "Aegis Cloud Run Service Account"
  depends_on   = [google_project_service.apis]
}

# Grant access to Secret Manager (Least Privilege)
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "gemini_secret_accessor" {
  secret_id = "GEMINI_API_KEY"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant access to GCS (Least Privilege)
resource "google_storage_bucket_iam_member" "storage_user" {
  bucket = google_storage_bucket.document_store.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant access to Cloud SQL
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant access to Vertex AI
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant access to Cloud Logging
resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}
