resource "google_project_service" "cloudrun" {
  service = "run.googleapis.com"

  disable_on_destroy = false
}

data "google_iam_policy" "default" {
  binding {
    role = "roles/run.invoker"
    members = [
      data.google_service_account.apigateway.member
    ]
  }
}

resource "google_cloud_run_v2_service" "default" {
  name     = local.service_name
  location = local.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    service_account = google_service_account.service.email

    containers {
      name = "app"
      # Note: This is not the actual image of the service as container lifecycle is managed outside of terraform
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name = "ENABLE_CLOUD_LOGGING"
        value = "1"
      }

      env {
        name = "ENABLE_CLOUD_TRACE"
        value = "1"
      }

      env {
        name = "FIRESTORE_DATABASE"
        value = google_firestore_database.default.name
      }

      env {
        name = "JWT_ISSUER"
        value = "https://${local.domain}"
      }

      env {
        name = "JWT_PRIVATE_KEY"
        value_source {
          secret_key_ref {
            secret = google_secret_manager_secret.jwt_private_key.secret_id
            version = google_secret_manager_secret_version.jwt_private_key.version
          }
        }
      }

      startup_probe {
        http_get {
          path = "/api/v1/health/${local.service_name}"
        }
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health/${local.service_name}"
        }
      }

      resources {
        cpu_idle = true
        startup_cpu_boost = true
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image
    ] 
  }

  depends_on = [ google_project_service.cloudrun ]
}

resource "google_cloud_run_v2_service_iam_policy" "default" {
  project = google_cloud_run_v2_service.default.project
  location = google_cloud_run_v2_service.default.location
  name = google_cloud_run_v2_service.default.name
  policy_data = data.google_iam_policy.default.policy_data
}
