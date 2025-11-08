variable "eks_cluster_name" {
  description = "Name of the EKS cluster for the IAM role"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "eks_tags" {
  description = "AWS region"
  type = object({
    Purpose = string
  })
  default = { "Purpose" : "EKSCluster" }
}

