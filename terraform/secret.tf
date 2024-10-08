# Enables the Secret Manager API for the project.
resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Creates a Secret Manager secret to store the JWT private key.
data "google_secret_manager_secret" "jwt_private_key" {
  secret_id = "jwt-private-key"
}

data "google_secret_manager_secret_version" "jwt_private_key" {
  secret = data.google_secret_manager_secret.jwt_private_key.id
}

# Grants the service account (this microservice) read access to the JWT private key secret.
resource "google_secret_manager_secret_iam_member" "read_jwt_private_key" {
  secret_id = data.google_secret_manager_secret.jwt_private_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.service.member
}
