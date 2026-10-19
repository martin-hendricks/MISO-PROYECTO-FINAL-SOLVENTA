output "vpc_id" {
  value       = aws_vpc.this.id
  description = "VPC ID."
}

output "vpc_cidr_block" {
  value       = aws_vpc.this.cidr_block
  description = "VPC IPv4 CIDR (for security group rules)."
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs (ALB, NAT gateways)."
}

output "private_app_subnet_ids" {
  value       = aws_subnet.private_app[*].id
  description = "Private application subnet IDs (EKS node groups)."
}

output "private_data_subnet_ids" {
  value       = aws_subnet.private_data[*].id
  description = "Private data subnet IDs (RDS, ElastiCache, MSK)."
}

output "availability_zones" {
  value       = var.availability_zones
  description = "AZs used by this network."
}

output "nat_gateway_ids" {
  value       = aws_nat_gateway.this[*].id
  description = "NAT gateway IDs."
}
