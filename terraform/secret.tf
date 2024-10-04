resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"

  disable_on_destroy = false
}

resource "google_secret_manager_secret" "jwt_private_key" {
  secret_id = "jwt-private-key"
  replication {
    auto {}
  }

  depends_on = [ google_project_service.secretmanager ]
}

resource "google_secret_manager_secret_version" "jwt_private_key" {
  secret = google_secret_manager_secret.jwt_private_key.id

  secret_data = local.jwt_private_key
}

resource "google_secret_manager_secret_iam_member" "read_jwt_private_key" {
  secret_id = google_secret_manager_secret.jwt_private_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.service.member
}
