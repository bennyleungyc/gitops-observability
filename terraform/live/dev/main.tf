module "iam" {
  source           = "../../modules/iam"
  eks_cluster_name = var.eks_cluster_name
  environment      = var.environment
}

module "eks" {
  source           = "../../modules/eks"
  region           = var.region
  eks_cluster_role = module.iam.eks_cluster_role
  eks_node_role    = module.iam.eks_node_role
  eks_cluster_name = var.eks_cluster_name
  environment      = var.environment
}

