resource "google_project_service" "iam" {
  service = "iam.googleapis.com"

  disable_on_destroy = false
}

resource "google_service_account" "service" {
  account_id   = local.service_name
  display_name = "Service Account ${local.service_name}"

  depends_on = [ google_project_service.iam ]
}

data "google_service_account" "apigateway" {
  account_id   = "apigateway"

  depends_on = [ google_project_service.iam ]
}

data "google_service_account" "circleci" {
  account_id   = "circleci"

  depends_on = [ google_project_service.iam ]
}
