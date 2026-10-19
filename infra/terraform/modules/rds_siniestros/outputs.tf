output "db_instance_id" {
  value       = aws_db_instance.this.id
  description = "Identifier of the DBSiniestros instance."
}

output "db_instance_arn" {
  value       = aws_db_instance.this.arn
  description = "ARN of the DBSiniestros instance."
}

output "endpoint" {
  value       = aws_db_instance.this.address
  description = "Hostname (no port) of the instance. There is no reader_endpoint by design: the Multi-AZ standby is passive and never serves traffic (EC-DISP-06/07)."
}

output "db_name" {
  value       = aws_db_instance.this.db_name
  description = "Database name."
}

output "master_username" {
  value       = var.db_username
  sensitive   = true
  description = "Master username."
}

output "master_password" {
  value       = random_password.master.result
  sensitive   = true
  description = "Master password (also present in Terraform state)."
}

output "port" {
  value       = aws_db_instance.this.port
  description = "Database port."
}
