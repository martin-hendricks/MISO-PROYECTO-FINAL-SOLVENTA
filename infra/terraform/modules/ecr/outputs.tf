output "repository_urls" {
  value       = { for name, repo in aws_ecr_repository.this : name => repo.repository_url }
  description = "Map of component name to ECR repository URL, for use in k8s/ image references and CI/CD."
}

output "repository_arns" {
  value       = { for name, repo in aws_ecr_repository.this : name => repo.arn }
  description = "Map of component name to ECR repository ARN."
}
