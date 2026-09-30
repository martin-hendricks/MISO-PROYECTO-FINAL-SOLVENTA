locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  cluster_name = "${var.project_name}-${var.environment}-eks"
}

# ---------------------------------------------------------------------------
# IAM: rol del clúster
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "eks_cluster_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cluster" {
  name               = "${var.project_name}-${var.environment}-eks-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.eks_cluster_assume_role.json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-cluster-role" })
}

resource "aws_iam_role_policy_attachment" "cluster_eks_cluster_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role_policy_attachment" "cluster_vpc_resource_controller" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
}

# ---------------------------------------------------------------------------
# IAM: rol de los node groups
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "eks_node_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "node" {
  name               = "${var.project_name}-${var.environment}-eks-node-role"
  assume_role_policy = data.aws_iam_policy_document.eks_node_assume_role.json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-node-role" })
}

resource "aws_iam_role_policy_attachment" "node_worker_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_cni_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_ecr_read_only" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# ---------------------------------------------------------------------------
# Clúster EKS
# ---------------------------------------------------------------------------

resource "aws_eks_cluster" "this" {
  name     = local.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.private_app_subnet_ids
    security_group_ids      = var.node_security_group_ids
    endpoint_private_access = true
    endpoint_public_access  = var.endpoint_public_access
    public_access_cidrs     = var.endpoint_public_access ? var.public_access_cidrs : null
  }

  encryption_config {
    provider {
      key_arn = var.kms_key_arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler",
  ]

  tags = merge(local.common_tags, { Name = local.cluster_name })

  depends_on = [
    aws_iam_role_policy_attachment.cluster_eks_cluster_policy,
    aws_iam_role_policy_attachment.cluster_vpc_resource_controller,
  ]
}

# ---------------------------------------------------------------------------
# Proveedor OIDC (IRSA)
# ---------------------------------------------------------------------------

data "tls_certificate" "eks_oidc" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_oidc.certificates[0].sha1_fingerprint]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-oidc" })
}

# ---------------------------------------------------------------------------
# Node Group A: ms-cotizacion (MotorRating) + ms-perfilamiento (MotorRiesgo)
#
# Curvas de carga independientes, escalamiento vertical, warm pool y
# capacidad ampliada <= 60 s (EC-ESC-02). Aislado del resto de servicios con
# un taint opcional; los pods de estos dos microservicios deben declarar la
# toleración solventa.io/scaling-group=a:NoSchedule y el nodeSelector
# solventa.io/scaling-group=a en su manifiesto de Kubernetes.
# ---------------------------------------------------------------------------

resource "aws_eks_node_group" "grupo_a" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.project_name}-${var.environment}-grupo-a"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_app_subnet_ids

  instance_types = var.node_group_a_instance_types
  capacity_type  = var.node_group_a_capacity_type
  disk_size      = var.node_group_a_disk_size

  scaling_config {
    min_size     = var.node_group_a_min_size
    desired_size = var.node_group_a_desired_size
    max_size     = var.node_group_a_max_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    "solventa.io/scaling-group" = "a"
  }

  dynamic "taint" {
    for_each = var.node_group_a_taint_enabled ? [1] : []
    content {
      key    = "solventa.io/scaling-group"
      value  = "a"
      effect = "NO_SCHEDULE"
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-grupo-a" })

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_ecr_read_only,
  ]

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}

# ---------------------------------------------------------------------------
# Node Group B: resto de microservicios, BFFs y adaptadores
# ---------------------------------------------------------------------------

resource "aws_eks_node_group" "grupo_b" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.project_name}-${var.environment}-grupo-b"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_app_subnet_ids

  instance_types = var.node_group_b_instance_types
  capacity_type  = var.node_group_b_capacity_type
  disk_size      = var.node_group_b_disk_size

  scaling_config {
    min_size     = var.node_group_b_min_size
    desired_size = var.node_group_b_desired_size
    max_size     = var.node_group_b_max_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    "solventa.io/scaling-group" = "b"
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-grupo-b" })

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_ecr_read_only,
  ]

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}

# ---------------------------------------------------------------------------
# Add-ons gestionados de AWS
# ---------------------------------------------------------------------------

resource "aws_eks_addon" "vpc_cni" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "vpc-cni"
  addon_version               = lookup(var.addon_versions, "vpc-cni", null)
  resolve_conflicts_on_update = "OVERWRITE"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-addon-vpc-cni" })

  depends_on = [
    aws_eks_node_group.grupo_a,
    aws_eks_node_group.grupo_b,
  ]
}

resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "coredns"
  addon_version               = lookup(var.addon_versions, "coredns", null)
  resolve_conflicts_on_update = "OVERWRITE"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-addon-coredns" })

  depends_on = [
    aws_eks_node_group.grupo_a,
    aws_eks_node_group.grupo_b,
  ]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "kube-proxy"
  addon_version               = lookup(var.addon_versions, "kube-proxy", null)
  resolve_conflicts_on_update = "OVERWRITE"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-addon-kube-proxy" })

  depends_on = [
    aws_eks_node_group.grupo_a,
    aws_eks_node_group.grupo_b,
  ]
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = "aws-ebs-csi-driver"
  addon_version               = lookup(var.addon_versions, "aws-ebs-csi-driver", null)
  resolve_conflicts_on_update = "OVERWRITE"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-addon-ebs-csi-driver" })

  depends_on = [
    aws_eks_node_group.grupo_a,
    aws_eks_node_group.grupo_b,
  ]
}
