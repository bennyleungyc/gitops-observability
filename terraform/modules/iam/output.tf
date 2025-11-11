output "eks_cluster_role" {
  description = "EKS cluster IAM role for the control plane"
  value       = aws_iam_role.eks_cluster_role
}

output "eks_node_role" {
  description = "EKS node IAM role for worker nodes"
  value       = aws_iam_role.eks_node_role
}