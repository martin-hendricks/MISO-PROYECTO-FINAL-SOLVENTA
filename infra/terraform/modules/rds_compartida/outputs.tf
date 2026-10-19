output "db_instance_id" {
  value       = aws_db_instance.this.id
  description = "Identifier of the DBCompartida instance."
}

output "db_instance_arn" {
  value       = aws_db_instance.this.arn
  description = "ARN of the DBCompartida instance."
}

output "endpoint" {
  value       = aws_db_instance.this.address
  description = "Hostname (no port) of the instance. No reader_endpoint: this instance has no redundancy by design (see main.tf)."
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
