output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "Attach to the Application Load Balancer."
}

output "vpc_link_security_group_id" {
  value       = aws_security_group.vpc_link.id
  description = "Attach to the API Gateway VPC Link (edge module): it is the only principal the ALB's security group lets through (EC-SEG-07)."
}

output "eks_nodes_security_group_id" {
  value       = aws_security_group.eks_nodes.id
  description = "Attach to the EKS node groups (Grupo A y Grupo B)."
}

output "rds_security_group_id" {
  value       = aws_security_group.rds.id
  description = "Attach to the RDS instances (DBPolizas, DBSiniestros)."
}

output "redis_security_group_id" {
  value       = aws_security_group.redis.id
  description = "Attach to the ElastiCache Redis clusters (CacheOF, CacheOD)."
}

output "msk_security_group_id" {
  value       = aws_security_group.msk.id
  description = "Attach to the MSK cluster (BusEventos, ColaPagos, TopicoTelemetria)."
}
