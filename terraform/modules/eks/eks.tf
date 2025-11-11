resource "aws_eks_cluster" "example" {
  name = "${var.environment}-${var.eks_cluster_name}-eks-cluster"
  role_arn = var.eks_cluster_role.arn
  access_config {
    authentication_mode = "API_AND_CONFIG_MAP"
  }
//  role_arn = aws_iam_role.cluster.arn
  version  = "1.34"

  vpc_config {
    endpoint_private_access = true
    endpoint_public_access  = true

    subnet_ids = [
      var.aws_subnet.az1.id,
      var.aws_subnet.az2.id,
      var.aws_subnet.az3.id,
    ]
    public_access_cidrs     = ["0.0.0.0/0"]
  }

}

resource "aws_eks_addon" "vpc_cni" {
  cluster_name      = aws_eks_cluster.example.name
  addon_name        = "vpc-cni"
  addon_version     = "v1.18.1-eksbuild.1"  # Optional: pin compatible version
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [
    null_resource.wait_for_cluster
  ]
}

resource "aws_eks_node_group" "example_node_group" {
  cluster_name    = aws_eks_cluster.example.name
  node_group_name = "example_node_group"
  node_role_arn   = var.eks_node_role.arn
  instance_types = ["t3.medium"]
  subnet_ids = [
      var.aws_subnet.az1.id,
      var.aws_subnet.az2.id,
      var.aws_subnet.az3.id,
    ]

  scaling_config {
    desired_size = 2
    max_size     = 6
    min_size     = 2
  }

  update_config {
    max_unavailable = 1
  }
  depends_on = [
      aws_eks_addon.vpc_cni,
      null_resource.wait_for_cni,
      null_resource.wait_for_cluster,
  ]
}

# Wait for the EKS cluster to be fully ACTIVE
resource "null_resource" "wait_for_cluster" {
  depends_on = [aws_eks_cluster.example]

  provisioner "local-exec" {
    command = "aws eks wait cluster-active --name ${aws_eks_cluster.example.name} --region ${var.region}"
  }
}

resource "null_resource" "wait_for_cni" {
  depends_on = [aws_eks_addon.vpc_cni]

  provisioner "local-exec" {
    command = <<EOF
      echo "Waiting for vpc-cni addon to be ACTIVE..."
      aws eks wait addon-active \
        --cluster-name ${aws_eks_cluster.example.name} \
        --addon-name vpc-cni \
        --region ${var.region}
      echo "vpc-cni is ACTIVE"
    EOF
  }
}

locals {
  admin_map = { for a in var.eks_cluster_admins : a.user_name => a }
}

resource "aws_eks_access_entry" "admin" {
  for_each      = local.admin_map
  cluster_name  = aws_eks_cluster.example.name
  principal_arn = each.value.principal_arn
  type          = "STANDARD"
  depends_on    = [aws_eks_cluster.example]
}

resource "aws_eks_access_policy_association" "admin_policy" {
  for_each      = local.admin_map
  cluster_name  = aws_eks_cluster.example.name
  principal_arn = each.value.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope { type = "cluster" }

  depends_on = [aws_eks_access_entry.admin]
}


