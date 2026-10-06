output "cluster_name" {
  value       = aws_eks_cluster.this.name
  description = "EKS cluster name."
}

output "cluster_endpoint" {
  value       = aws_eks_cluster.this.endpoint
  description = "EKS API server endpoint."
}

output "cluster_arn" {
  value       = aws_eks_cluster.this.arn
  description = "EKS cluster ARN."
}

output "cluster_certificate_authority_data" {
  value       = aws_eks_cluster.this.certificate_authority[0].data
  description = "Base64-encoded certificate authority data for kubeconfig."
}

output "cluster_security_group_id" {
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
  description = "Security group ID that EKS creates and manages for cluster/node communication."
}

output "oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.eks.arn
  description = "ARN of the IAM OIDC provider, used to build IRSA trust policies (eks_addons module)."
}

output "oidc_provider_url" {
  value       = aws_iam_openid_connect_provider.eks.url
  description = "OIDC issuer URL (without https://), used in IRSA trust policy conditions."
}

output "node_group_a_arn" {
  value       = aws_eks_node_group.grupo_a.arn
  description = "ARN of grupo-a node group (ms-cotizacion / ms-perfilamiento)."
}

output "node_group_b_arn" {
  value       = aws_eks_node_group.grupo_b.arn
  description = "ARN of grupo-b node group (resto de microservicios, BFFs y adaptadores)."
}
