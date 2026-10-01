variable "project_id" {
  type        = string
  description = "The GCP Project ID"
}

variable "region" {
  type        = string
  description = "The GCP Region"
  default     = "us-central1"
}

variable "db_password" {
  type        = string
  description = "The password for the PostgreSQL database user"
  sensitive   = true
}

variable "environment" {
  type        = string
  description = "The deployment environment (e.g., staging, production)"
  default     = "staging"
}
