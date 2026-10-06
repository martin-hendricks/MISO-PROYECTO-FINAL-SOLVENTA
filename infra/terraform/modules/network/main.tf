locals {
  az_count = length(var.availability_zones)

  # 3 tiers (public, private-app, private-data) x N AZs. newbits = 4 carves the
  # /16 VPC into /20 blocks (16 possible), enough headroom for up to 5 AZs per
  # tier without CIDR overlap between tiers.
  subnet_newbits = 4

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  create_cluster_tag = var.cluster_name != ""

  public_subnet_tags = merge(
    { "kubernetes.io/role/elb" = "1" },
    local.create_cluster_tag ? { "kubernetes.io/cluster/${var.cluster_name}" = "shared" } : {}
  )

  private_app_subnet_tags = merge(
    { "kubernetes.io/role/internal-elb" = "1" },
    local.create_cluster_tag ? { "kubernetes.io/cluster/${var.cluster_name}" = "shared" } : {}
  )
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-vpc" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-igw" })
}

# --- Subnets: public (ALB, NAT), private-app (EKS node groups), private-data (RDS, ElastiCache, MSK) ---

resource "aws_subnet" "public" {
  count = local.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, local.subnet_newbits, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, local.public_subnet_tags, {
    Name = "${var.project_name}-${var.environment}-public-${var.availability_zones[count.index]}"
    Tier = "public"
  })
}

resource "aws_subnet" "private_app" {
  count = local.az_count

  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, local.subnet_newbits, count.index + local.az_count)
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, local.private_app_subnet_tags, {
    Name = "${var.project_name}-${var.environment}-private-app-${var.availability_zones[count.index]}"
    Tier = "private-app"
  })
}

resource "aws_subnet" "private_data" {
  count = local.az_count

  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, local.subnet_newbits, count.index + (2 * local.az_count))
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-private-data-${var.availability_zones[count.index]}"
    Tier = "private-data"
  })
}

# --- NAT gateways (in public subnets) for private tier egress ---

resource "aws_eip" "nat" {
  count = var.single_nat_gateway ? 1 : local.az_count

  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.this]
}

resource "aws_nat_gateway" "this" {
  count = var.single_nat_gateway ? 1 : local.az_count

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.this]
}

# --- Route tables: one public, one per AZ for each private tier ---

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-public-rt" })
}

resource "aws_route_table_association" "public" {
  count = local.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private_app" {
  count = local.az_count

  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-private-app-rt-${var.availability_zones[count.index]}"
  })
}

resource "aws_route_table_association" "private_app" {
  count = local.az_count

  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private_app[count.index].id
}

resource "aws_route_table" "private_data" {
  count = local.az_count

  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-private-data-rt-${var.availability_zones[count.index]}"
  })
}

resource "aws_route_table_association" "private_data" {
  count = local.az_count

  subnet_id      = aws_subnet.private_data[count.index].id
  route_table_id = aws_route_table.private_data[count.index].id
}

# --- VPC Flow Logs (CloudWatch) ---

resource "aws_cloudwatch_log_group" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name              = "/${var.project_name}/${var.environment}/vpc-flow-logs"
  retention_in_days = var.flow_logs_retention_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-vpc-flow-logs" })
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name = "${var.project_name}-${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name = "${var.project_name}-${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
      ]
      Resource = "*"
    }]
  })
}

resource "aws_flow_log" "this" {
  count = var.enable_flow_logs ? 1 : 0

  vpc_id               = aws_vpc.this.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow_logs[0].arn
  iam_role_arn         = aws_iam_role.flow_logs[0].arn

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-vpc-flow-log" })
}
