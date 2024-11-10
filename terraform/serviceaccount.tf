# Enables the IAM API for the project.
resource "google_project_service" "iam" {
  service = "iam.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Creates a service account for this microservice.
resource "google_service_account" "service" {
  account_id   = local.service_name
  display_name = "Service Account ${local.service_name}"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the API Gateway.
# This is defined as part of the core infrastructure and is shared across all microservices.
data "google_service_account" "apigateway" {
  account_id   = "apigateway"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the CircleCI service account.
# This is defined as part of the core infrastructure and is shared across all microservices.
# This service account is used by CircleCI to deploy the microservice to Cloud Run.
data "google_service_account" "circleci" {
  account_id   = "circleci"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the user microservice.
# This is defined as part of the user microservice
# This service account is given permissions to access this microservice
data "google_service_account" "user" {
  account_id   = "user-svc"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the incidentquery microservice.
# This is defined as part of the incidentquery microservice
# This service account is given permissions to access this microservice
data "google_service_account" "incidentquery" {
  account_id   = "incidentquery"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the incidentmodify microservice.
# This is defined as part of the incidentmodify microservice
# This service account is given permissions to access this microservice
data "google_service_account" "incidentmodify" {
  account_id   = "incidentmodify"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the backup service account.
# This is defined as part of the core infrastructure and is shared across all microservices.
# This service account is used by the Cloud Scheduler to do database backups.
data "google_service_account" "backup" {
  account_id   = "backup"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the registroapp microservice.
# This is defined as part of the registroapp microservice
# This service account is given permissions to access this microservice
data "google_service_account" "registroapp" {
  account_id   = "registroapp"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the invoice microservice.
# This is defined as part of the invoice microservice
# This service account is given permissions to access this microservice
data "google_service_account" "invoice" {
  account_id   = "invoice"

  depends_on = [ google_project_service.iam ]
}

# Retrieves the service account of the registromail microservice.
# This is defined as part of the registromail microservice
# This service account is given permissions to access this microservice
data "google_service_account" "registromail" {
  account_id   = "registromail"

  depends_on = [ google_project_service.iam ]
}
