resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL_${var.environment}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url_data" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+asyncpg://postgres:${var.db_password}@/aegis?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}
