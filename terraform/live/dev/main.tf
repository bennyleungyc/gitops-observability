terraform {
  backend "s3" {
    bucket  = "argocd-eks-cluster"
    key     = "dev/terraform.tfstate"
    region  = "ap-southeast-1"
    encrypt = true
  }
}

module "iam" {
  source           = "../../modules/iam"
  eks_cluster_name = var.eks_cluster_name
  environment      = var.environment
}

module "eks" {
  source             = "../../modules/eks"
  region             = var.region
  eks_cluster_role   = module.iam.eks_cluster_role
  eks_node_role      = module.iam.eks_node_role
  eks_cluster_name   = var.eks_cluster_name
  environment        = var.environment
  aws_subnet         = var.aws_subnet
  eks_cluster_admins = var.eks_cluster_admins
}

