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

  access_config {
    authentication_mode = "API_AND_CONFIG_MAP"
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
# IRSA del add-on EBS CSI driver
#
# Sin este rol, el pod ebs-csi-controller intenta autenticarse vía IMDS del
# nodo EC2 y falla en CrashLoopBackOff con "no EC2 IMDS role found": el add-on
# gestionado necesita su propio ServiceAccount con un rol IRSA, igual que los
# add-ons de Helm en modules/eks_addons (ALB Controller, Cluster Autoscaler,
# External Secrets), pero aquí se cablea directo en aws_eks_addon en vez de
# vía "helm set", porque EKS gestiona la anotación del ServiceAccount por su
# cuenta a partir de service_account_role_arn.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ebs_csi_driver_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ebs_csi_driver" {
  name               = "${var.project_name}-${var.environment}-ebs-csi-driver-irsa"
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_driver_assume_role.json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-ebs-csi-driver-irsa" })
}

# Política gestionada oficial de AWS para el driver, en vez de una política
# propia: es la ruta recomendada por AWS y ya cubre exactamente los permisos
# de EBS (CreateVolume, AttachVolume, snapshots, etc.) que el driver necesita.
resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  role       = aws_iam_role.ebs_csi_driver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

# ---------------------------------------------------------------------------
# Launch templates — adjuntan el SG personalizado a los nodos
# ---------------------------------------------------------------------------
#
# Un managed node group SIN launch_template propio solo recibe el security
# group automático que EKS crea para el cluster (eks-cluster-sg-...); el
# contenido de var.node_security_group_ids nunca llega a las instancias
# EC2 reales por esa vía -- solo se usa en aws_eks_cluster.vpc_config, que
# es la ENI del control plane, no la de los nodos worker. Sin este launch
# template, RDS/Redis/MSK (cuyos security groups de datos autorizan
# explícitamente el SG personalizado "eks-nodes", no el automático del
# cluster) rechazan toda conexión de los pods con un timeout, no un
# "connection refused" -- el timeout es la pista de que es un problema de
# red/SG, no de credenciales de la app.
#
# Un launch template por grupo (no uno compartido) porque instance_type y
# el tamaño de disco difieren entre grupo-a y grupo-b, y AWS exige que esos
# dos campos se fijen en el launch template -- no en aws_eks_node_group --
# en cuanto el node group usa un launch_template.
#
# image_id vacío a propósito: EKS sigue resolviendo la AMI optimizada y el
# bootstrap automáticamente para managed node groups; el launch template
# solo existe aquí para fijar instance_type/disco (ya requerido por AWS) y
# añadir el SG adicional a la interfaz de red.
resource "aws_launch_template" "grupo_a" {
  name_prefix   = "${var.project_name}-${var.environment}-eks-grupo-a-"
  instance_type = var.node_group_a_instance_types[0]

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.node_group_a_disk_size
      delete_on_termination = true
    }
  }

  network_interfaces {
    security_groups             = var.node_security_group_ids
    delete_on_termination       = true
    associate_public_ip_address = false
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-grupo-a-node" })
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-grupo-a-lt" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_launch_template" "grupo_b" {
  name_prefix   = "${var.project_name}-${var.environment}-eks-grupo-b-"
  instance_type = var.node_group_b_instance_types[0]

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.node_group_b_disk_size
      delete_on_termination = true
    }
  }

  network_interfaces {
    security_groups             = var.node_security_group_ids
    delete_on_termination       = true
    associate_public_ip_address = false
  }

  tag_specifications {
    resource_type = "instance"
    tags          = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-grupo-b-node" })
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-grupo-b-lt" })

  lifecycle {
    create_before_destroy = true
  }
}

# ---------------------------------------------------------------------------
# Node Group A: ms-cotizacion (MotorRating) + ms-perfilamiento (MotorRiesgo)
#
# Curvas de carga independientes, escalamiento vertical e imágenes livianas
# para ganar los primeros segundos de la rampa, con capacidad ampliada
# <= 60 s (EC-ESC-02). No hay warm pool: los managed node groups de EKS no
# soportan esa feature (es propia de Auto Scaling Groups self-managed). Está
# aislado del resto de servicios con
# un taint opcional; los pods de estos dos microservicios deben declarar la
# toleración solventa.io/scaling-group=a:NoSchedule y el nodeSelector
# solventa.io/scaling-group=a en su manifiesto de Kubernetes.
# ---------------------------------------------------------------------------

resource "aws_eks_node_group" "grupo_a" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.project_name}-${var.environment}-grupo-a"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_app_subnet_ids

  launch_template {
    id      = aws_launch_template.grupo_a.id
    version = aws_launch_template.grupo_a.latest_version
  }

  # instance_types/disk_size NO van aquí: ya están fijados en el launch
  # template (aws_launch_template.grupo_a). AWS rechaza especificarlos en
  # ambos lados cuando el node group usa un launch_template.
  capacity_type = var.node_group_a_capacity_type

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

  launch_template {
    id      = aws_launch_template.grupo_b.id
    version = aws_launch_template.grupo_b.latest_version
  }

  # instance_types/disk_size NO van aquí: ya están fijados en el launch
  # template (aws_launch_template.grupo_b). AWS rechaza especificarlos en
  # ambos lados cuando el node group usa un launch_template.
  capacity_type = var.node_group_b_capacity_type

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
  service_account_role_arn    = aws_iam_role.ebs_csi_driver.arn

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-addon-ebs-csi-driver" })

  depends_on = [
    aws_eks_node_group.grupo_a,
    aws_eks_node_group.grupo_b,
    aws_iam_role_policy_attachment.ebs_csi_driver,
  ]
}

# ---------------------------------------------------------------------------
# Acceso de administrador para quien aplica Terraform
# ---------------------------------------------------------------------------
#
# Con authentication_mode = API_AND_CONFIG_MAP, a diferencia del modo legado
# basado solo en el ConfigMap aws-auth, crear el clúster ya NO otorga
# system:masters implícito al principal de IAM que lo creó. Sin este access
# entry, el provider helm (y cualquier kubectl manual) recibe "the server
# has asked for the client to provide credentials" aunque las credenciales
# de AWS sean válidas: son válidas para IAM, pero no están autorizadas
# dentro de la API de Kubernetes.
data "aws_caller_identity" "current" {}

resource "aws_eks_access_entry" "terraform_admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = data.aws_caller_identity.current.arn
  type          = "STANDARD"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-eks-terraform-admin" })
}

resource "aws_eks_access_policy_association" "terraform_admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = data.aws_caller_identity.current.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.terraform_admin]
}
