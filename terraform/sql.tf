resource "google_sql_database_instance" "postgres" {
  name             = "aegis-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro" # Standard micro for staging, scale for prod

    ip_configuration {
      ipv4_enabled = true
      # In production, require private VPC, but for this demo using public IP 
      # with authorized networks or Cloud Run VPC connector
    }
  }

  deletion_protection = false # Set to true in prod!
  depends_on          = [google_project_service.apis]
}

resource "google_sql_database" "aegis_db" {
  name     = "aegis"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "postgres" {
  name     = "postgres"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}
