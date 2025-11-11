variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "argocd"
}

variable "environment" {
  description = "Environment Type"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Environment Type"
  type        = string
  default     = "ap-southeast-1"
}

variable "eks_cluster_admins" {
  type = list(object({
    principal_arn = string
    user_name     = string
  }))
  default = []
}