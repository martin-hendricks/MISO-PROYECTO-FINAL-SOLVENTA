output "role_arn" {
  value       = aws_iam_role.github_actions_cd.arn
  description = "ARN to use as `role-to-assume` in aws-actions/configure-aws-credentials, from the GitHub Actions workflow."
}

output "role_name" {
  value       = aws_iam_role.github_actions_cd.name
  description = "Name of the IAM role assumed by GitHub Actions."
}

output "oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.github_actions.arn
  description = "ARN of the GitHub Actions OIDC provider. Only one per AWS account; reuse this output if other roles need to trust GitHub Actions too, rather than registering the provider again."
}
