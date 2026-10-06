output "log_group_names" {
  value       = { for k, v in aws_cloudwatch_log_group.microservices : k => v.name }
  description = "Map of microservice/component name to its CloudWatch log group name."
}

output "sns_topic_arn" {
  value       = aws_sns_topic.alarms.arn
  description = "ARN of the SNS topic used by all CloudWatch alarms in this module."
}

output "dashboard_name" {
  value       = aws_cloudwatch_dashboard.this.dashboard_name
  description = "Name of the CloudWatch dashboard grouping ALB/RDS/ElastiCache/MSK metrics."
}

output "prometheus_workspace_id" {
  value       = var.enable_managed_prometheus ? aws_prometheus_workspace.this[0].id : ""
  description = "ID of the Amazon Managed Prometheus workspace, empty string when enable_managed_prometheus is false."
}
