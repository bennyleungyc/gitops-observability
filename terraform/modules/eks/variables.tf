variable "aws_subnet" {
  type = object({
    az1 = object({
      id = string
    })
    az2 = object({
      id = string
    })
    az3 = object({
      id = string
    })
  })
  description = "Subnet IDs for different availability zones"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster for the IAM role"
  type        = string
}

variable "eks_cluster_role" {
  description = "IAM role for the EKS cluster control plane"
  type        = any
}

variable "eks_node_role" {
  description = "IAM role for the EKS worker nodes"
  type        = any
}

variable "region" {
  description = "Region"
  type        = string
}