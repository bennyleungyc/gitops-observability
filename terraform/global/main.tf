terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" # Pins to latest 6.x version; adjust as needed
    }
  }
}

provider "aws" {
  region = "us-west-2" # Default region for resources
}