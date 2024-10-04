terraform {
  required_providers {
    google = {
      version = "~> 6.4.0"
    }
  }
}

terraform {
  backend "gcs" {
    prefix = "service-client/state"
  }
}

provider "google" {
  project = local.project_id
  region  = local.region
}
