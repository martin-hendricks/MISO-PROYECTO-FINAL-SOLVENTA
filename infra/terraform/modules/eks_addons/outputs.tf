output "aws_load_balancer_controller_role_arn" {
  value       = var.enable_aws_load_balancer_controller ? aws_iam_role.lb_controller[0].arn : null
  description = "IRSA role ARN used by the AWS Load Balancer Controller, or null if disabled."
}

output "cluster_autoscaler_role_arn" {
  value       = var.enable_cluster_autoscaler ? aws_iam_role.cluster_autoscaler[0].arn : null
  description = "IRSA role ARN used by the Cluster Autoscaler, or null if disabled."
}

output "external_secrets_role_arn" {
  value       = var.enable_external_secrets ? aws_iam_role.external_secrets[0].arn : null
  description = "IRSA role ARN used by the External Secrets Operator, or null if disabled."
}
