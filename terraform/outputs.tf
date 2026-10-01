output "cloudrun_url" {
  value = google_cloud_run_v2_service.aegis_api.uri
}

output "database_private_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}

output "service_account_email" {
  value = google_service_account.cloudrun_sa.email
}

output "artifact_registry_repo" {
  value = google_artifact_registry_repository.aegis_repo.id
}
