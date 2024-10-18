# Enables the Cloud Scheduler API for the project.
resource "google_project_service" "cloudscheduler" {
  service = "cloudscheduler.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Creates a Cloud Scheduler job, that pings the health endpoint of this microservice every minute.
# This is used to keep the service warm and prevent it from being scaled down to zero instances.
resource "google_cloud_scheduler_job" "default" {
  name             = "ping-${local.service_name}"
  region           = local.region
  schedule         = "* * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "30s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "GET"
    uri         = "https://${local.domain}/api/v1/health/${local.service_name}"
  }

  depends_on = [ google_project_service.cloudscheduler ]
}

# Creates a Cloud Scheduler job, that backups the firestore database daily.
resource "google_cloud_scheduler_job" "backup" {
  name             = "backup-${local.service_name}"
  region           = local.region
  schedule         = "30 7 * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "30s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://${local.service_name}-${data.google_project.default.number}.${local.region}.run.app/api/v1/backup/${local.service_name}"
    oidc_token {
      service_account_email = data.google_service_account.backup.email
      audience = "https://${local.service_name}-${data.google_project.default.number}.${local.region}.run.app"
    }
  }

  depends_on = [ google_project_service.cloudscheduler ]
}
