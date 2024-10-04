resource "google_project_service" "cloudscheduler" {
  service = "cloudscheduler.googleapis.com"

  disable_on_destroy = false
}

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
