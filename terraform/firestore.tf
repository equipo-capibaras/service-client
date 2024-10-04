resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_iam_member" "firestore" {
  project = local.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.service.member
}

resource "google_firestore_database" "default" {
  name                    = local.service_name
  location_id             = local.region
  type                    = "FIRESTORE_NATIVE"
  deletion_policy         = "DELETE"
  delete_protection_state = "DELETE_PROTECTION_DISABLED"

  depends_on = [ google_project_service.firestore ]
}

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
