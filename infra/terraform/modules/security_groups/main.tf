locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

# --- Security groups (empty shells; rules below as separate aws_security_group_rule
# resources to avoid dependency cycles between alb <-> eks_nodes) ---

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb"
  description = "Application Load Balancer, internal -- only reachable from the API Gateway VPC Link (EC-SEG-07: no direct bypass of the gateway/WAF)"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-alb" })
}

resource "aws_security_group" "vpc_link" {
  name        = "${var.project_name}-${var.environment}-apigw-vpclink"
  description = "API Gateway VPC Link ENIs -- the only principal allowed to reach the internal ALB"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-apigw-vpclink" })
}

resource "aws_security_group_rule" "vpc_link_egress_to_alb" {
  type                     = "egress"
  description              = "To the internal ALB on 80/443"
  security_group_id        = aws_security_group.vpc_link.id
  from_port                = 80
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

resource "aws_security_group" "eks_nodes" {
  name        = "${var.project_name}-${var.environment}-eks-nodes"
  description = "EKS worker nodes (application tier)"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-eks-nodes" })
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds"
  description = "RDS PostgreSQL (DBPolizas, DBSiniestros)"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-rds" })
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis"
  description = "ElastiCache Redis (CacheOF, CacheOD)"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-redis" })
}

resource "aws_security_group" "msk" {
  name        = "${var.project_name}-${var.environment}-msk"
  description = "MSK Kafka brokers (BusEventos, ColaPagos, TopicoTelemetria)"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg-msk" })
}

# --- alb rules ---

# EC-SEG-07: el ALB solo acepta tráfico del VPC Link del API Gateway, no de
# 0.0.0.0/0. Antes aceptaba cualquier IP en 80/443, lo que permitía llamarlo
# directo saltándose el API Gateway y su WAF/throttling por completo.
resource "aws_security_group_rule" "alb_ingress_http" {
  type                     = "ingress"
  description              = "HTTP from the API Gateway VPC Link only"
  security_group_id        = aws_security_group.alb.id
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.vpc_link.id
}

resource "aws_security_group_rule" "alb_ingress_https" {
  type                     = "ingress"
  description              = "HTTPS from the API Gateway VPC Link only"
  security_group_id        = aws_security_group.alb.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.vpc_link.id
}

resource "aws_security_group_rule" "alb_egress_to_eks_nodes" {
  type                     = "egress"
  description              = "To EKS nodes on NodePort range"
  security_group_id        = aws_security_group.alb.id
  from_port                = var.node_port_range_start
  to_port                  = var.node_port_range_end
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

# --- eks_nodes rules ---

resource "aws_security_group_rule" "eks_nodes_ingress_from_alb" {
  type                     = "ingress"
  description              = "NodePort range from the ALB"
  security_group_id        = aws_security_group.eks_nodes.id
  from_port                = var.node_port_range_start
  to_port                  = var.node_port_range_end
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "eks_nodes_ingress_self" {
  type              = "ingress"
  description       = "Pod-to-pod communication between nodes"
  security_group_id = aws_security_group.eks_nodes.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  self              = true
}

resource "aws_security_group_rule" "eks_nodes_egress_all" {
  type              = "egress"
  description       = "All outbound"
  security_group_id = aws_security_group.eks_nodes.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}

# --- rds rules (DBPolizas, DBSiniestros) ---

resource "aws_security_group_rule" "rds_ingress_from_eks_nodes" {
  type                     = "ingress"
  description              = "PostgreSQL from EKS nodes only"
  security_group_id        = aws_security_group.rds.id
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_security_group_rule" "rds_egress_all" {
  type              = "egress"
  description       = "All outbound"
  security_group_id = aws_security_group.rds.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}

# --- redis rules (CacheOF, CacheOD) ---

resource "aws_security_group_rule" "redis_ingress_from_eks_nodes" {
  type                     = "ingress"
  description              = "Redis from EKS nodes only"
  security_group_id        = aws_security_group.redis.id
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_security_group_rule" "redis_egress_all" {
  type              = "egress"
  description       = "All outbound"
  security_group_id = aws_security_group.redis.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}

# --- msk rules (BusEventos, ColaPagos, TopicoTelemetria) ---

resource "aws_security_group_rule" "msk_ingress_plaintext_from_eks_nodes" {
  type                     = "ingress"
  description              = "Kafka plaintext broker from EKS nodes only"
  security_group_id        = aws_security_group.msk.id
  from_port                = 9092
  to_port                  = 9092
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_security_group_rule" "msk_ingress_tls_from_eks_nodes" {
  type                     = "ingress"
  description              = "Kafka TLS broker from EKS nodes only"
  security_group_id        = aws_security_group.msk.id
  from_port                = 9094
  to_port                  = 9094
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_security_group_rule" "msk_ingress_zookeeper_from_eks_nodes" {
  type                     = "ingress"
  description              = "Zookeeper from EKS nodes only"
  security_group_id        = aws_security_group.msk.id
  from_port                = 2181
  to_port                  = 2181
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_security_group_rule" "msk_egress_all" {
  type              = "egress"
  description       = "All outbound"
  security_group_id = aws_security_group.msk.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}
