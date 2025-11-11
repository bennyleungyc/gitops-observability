module "iam" {
  source           = "../../modules/iam"
  eks_cluster_name = var.eks_cluster_name
  environment      = var.environment
}

module "eks" {
  source           = "../../modules/eks"
  aws_subnet = {
    az1: {id = "subnet-a9c314cf"},
    az2: {id = "subnet-dce86a85"},
    az3: {id = "subnet-ab8d4ae3"}
  }
  region           = var.region
  eks_cluster_role = module.iam.eks_cluster_role
  eks_node_role    = module.iam.eks_node_role
  eks_cluster_name = var.eks_cluster_name
  environment      = var.environment
}

