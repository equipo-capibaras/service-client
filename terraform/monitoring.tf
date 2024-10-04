resource "google_project_service" "cloudtrace" {
  service = "cloudtrace.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_iam_member" "cloudtrace" {
  project = local.project_id
  role    = "roles/cloudtrace.agent"
  member  = google_service_account.service.member

  depends_on = [ google_project_service.cloudtrace ]
}
