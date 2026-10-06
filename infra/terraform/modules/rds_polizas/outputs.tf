output "db_instance_id" {
  value       = aws_db_instance.this.id
  description = "Identifier of the primary DBPolizas instance."
}

output "db_instance_arn" {
  value       = aws_db_instance.this.arn
  description = "ARN of the primary DBPolizas instance."
}

output "writer_endpoint" {
  value       = aws_db_instance.this.address
  description = "Hostname (no port) of the primary instance, for writes and reads that require the freshest data."
}

output "reader_endpoint" {
  value       = var.create_read_replica ? aws_db_instance.read_replica[0].address : null
  description = "Hostname (no port) of the active read replica (EC-LAT-10). This replica serves real production read traffic, not just a passive standby -- consumers should point read-heavy queries here."
}

output "reader_instance_id" {
  value       = var.create_read_replica ? aws_db_instance.read_replica[0].id : null
  description = "Identifier of the active read replica, for CloudWatch dimensions (e.g. the ReplicaLag alarm in the observability module). Null when create_read_replica is false."
}

output "db_name" {
  value       = aws_db_instance.this.db_name
  description = "Database name."
}

output "master_username" {
  value       = var.db_username
  sensitive   = true
  description = "Master username of the primary instance."
}

output "master_password" {
  value       = random_password.master.result
  sensitive   = true
  description = "Master password of the primary instance (also present in Terraform state)."
}

output "port" {
  value       = aws_db_instance.this.port
  description = "Database port, shared by primary and replica."
}

output "security_group_ids" {
  value       = var.vpc_security_group_ids
  description = "Security group ids applied to the primary and the read replica."
}
