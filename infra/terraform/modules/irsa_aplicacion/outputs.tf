output "role_arns" {
  value       = { for k, r in aws_iam_role.this : k => r.arn }
  description = "Map of component name to IRSA role ARN. Each value goes into serviceAccount.roleArn of the matching file in infra/k8s/values/."
}

output "role_names" {
  value       = { for k, r in aws_iam_role.this : k => r.name }
  description = "Map of component name to IAM role name."
}

output "service_account_annotations" {
  value = {
    for k, r in aws_iam_role.this : k => {
      "eks.amazonaws.com/role-arn" = r.arn
    }
  }
  description = "Ready-to-use ServiceAccount annotation per component, in the form the EKS pod identity webhook expects."
}
