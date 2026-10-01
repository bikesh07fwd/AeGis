resource "google_storage_bucket" "document_store" {
  name          = "${var.project_id}-aegis-docs-${var.environment}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  depends_on = [google_project_service.apis]
}
