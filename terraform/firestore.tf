# Enables the Firestore API for the project.
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Grants the service account the "Datastore User" role on the project.
# This allows the service account (this microservice) to access the firestore database.
resource "google_project_iam_member" "firestore" {
  project = local.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.service.member
}

# Grants the service account the "Datastore Import/Export Admin" role on the project.
# This allows the service account to backup the firestore database.
resource "google_project_iam_member" "firestore_backup" {
  project = local.project_id
  role    = "roles/datastore.importExportAdmin"
  member  = google_service_account.service.member
}

# Creates a Firestore database for this microservice.
resource "google_firestore_database" "default" {
  name                              = local.service_name
  location_id                       = local.region
  type                              = "FIRESTORE_NATIVE"
  deletion_policy                   = "DELETE"
  delete_protection_state           = "DELETE_PROTECTION_DISABLED"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"

  depends_on = [ google_project_service.firestore ]
}

# Creates a single field index on the "employees" collection for the "email" field.
# This is used to find a specific employee by their email address across all clients.
resource "google_firestore_field" "idx_employees_email" {
  database   = google_firestore_database.default.name
  collection = "employees"
  field      = "email"

  index_config {
    indexes {
        order = "ASCENDING"
        query_scope = "COLLECTION_GROUP"
    }
  }
}
