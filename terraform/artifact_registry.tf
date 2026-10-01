resource "google_artifact_registry_repository" "aegis_repo" {
  location      = var.region
  repository_id = "aegis-${var.environment}"
  description   = "Docker repository for Aegis AI"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}
