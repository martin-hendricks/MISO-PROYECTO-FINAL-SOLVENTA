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

# ---------------------------------------------------------------------------
# AWS Load Balancer Controller
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "lb_controller_assume_role" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lb_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  name               = "${var.project_name}-${var.environment}-lb-controller-irsa"
  assume_role_policy = data.aws_iam_policy_document.lb_controller_assume_role[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-lb-controller-irsa" })
}

data "aws_iam_policy_document" "lb_controller_permissions" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  statement {
    sid    = "ELBAndEC2Read"
    effect = "Allow"
    actions = [
      "ec2:DescribeAccountAttributes",
      "ec2:DescribeAddresses",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeInternetGateways",
      "ec2:DescribeVpcs",
      "ec2:DescribeVpcPeeringConnections",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeInstances",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeTags",
      "ec2:DescribeCoipPools",
      "ec2:GetCoipPoolUsage",
      "elasticloadbalancing:DescribeLoadBalancers",
      "elasticloadbalancing:DescribeLoadBalancerAttributes",
      "elasticloadbalancing:DescribeListeners",
      "elasticloadbalancing:DescribeListenerCertificates",
      "elasticloadbalancing:DescribeSSLPolicies",
      "elasticloadbalancing:DescribeRules",
      "elasticloadbalancing:DescribeTargetGroups",
      "elasticloadbalancing:DescribeTargetGroupAttributes",
      "elasticloadbalancing:DescribeTargetHealth",
      "elasticloadbalancing:DescribeTags",
      "wafv2:GetWebACL",
      "wafv2:GetWebACLForResource",
      "wafv2:AssociateWebACL",
      "wafv2:DisassociateWebACL",
      "shield:GetSubscriptionState",
      "shield:DescribeProtection",
      "shield:CreateProtection",
      "shield:DeleteProtection",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "EC2SecurityGroupWrite"
    effect = "Allow"
    actions = [
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:CreateSecurityGroup",
      "ec2:CreateTags",
      "ec2:DeleteTags",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ELBWrite"
    effect = "Allow"
    actions = [
      "elasticloadbalancing:CreateLoadBalancer",
      "elasticloadbalancing:CreateTargetGroup",
      "elasticloadbalancing:CreateListener",
      "elasticloadbalancing:CreateRule",
      "elasticloadbalancing:DeleteLoadBalancer",
      "elasticloadbalancing:DeleteTargetGroup",
      "elasticloadbalancing:DeleteListener",
      "elasticloadbalancing:DeleteRule",
      "elasticloadbalancing:ModifyLoadBalancerAttributes",
      "elasticloadbalancing:ModifyTargetGroup",
      "elasticloadbalancing:ModifyTargetGroupAttributes",
      "elasticloadbalancing:ModifyListener",
      "elasticloadbalancing:ModifyRule",
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:RemoveTags",
      "elasticloadbalancing:RegisterTargets",
      "elasticloadbalancing:DeregisterTargets",
      "elasticloadbalancing:SetIpAddressType",
      "elasticloadbalancing:SetSecurityGroups",
      "elasticloadbalancing:SetSubnets",
      "elasticloadbalancing:SetWebAcl",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "IAMServiceLinkedRole"
    effect    = "Allow"
    actions   = ["iam:CreateServiceLinkedRole"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values   = ["elasticloadbalancing.amazonaws.com"]
    }
  }

  statement {
    sid       = "ACMAndCognito"
    effect    = "Allow"
    actions   = ["acm:DescribeCertificate", "acm:ListCertificates", "acm:GetCertificate", "cognito-idp:DescribeUserPoolClient"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lb_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  name        = "${var.project_name}-${var.environment}-lb-controller-policy"
  description = "Permissions required by the AWS Load Balancer Controller (ELB, EC2, WAFv2)."
  policy      = data.aws_iam_policy_document.lb_controller_permissions[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-lb-controller-policy" })
}

resource "aws_iam_role_policy_attachment" "lb_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  role       = aws_iam_role.lb_controller[0].name
  policy_arn = aws_iam_policy.lb_controller[0].arn
}

resource "helm_release" "aws_load_balancer_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = var.aws_load_balancer_controller_chart_version
  namespace  = "kube-system"

  set {
    name  = "clusterName"
    value = var.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.lb_controller[0].arn
  }

  set {
    name  = "vpcId"
    value = var.vpc_id
  }

  set {
    name  = "region"
    value = var.aws_region
  }

  depends_on = [aws_iam_role_policy_attachment.lb_controller]
}

# ---------------------------------------------------------------------------
# Cluster Autoscaler
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "cluster_autoscaler_assume_role" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:kube-system:cluster-autoscaler"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  name               = "${var.project_name}-${var.environment}-cluster-autoscaler-irsa"
  assume_role_policy = data.aws_iam_policy_document.cluster_autoscaler_assume_role[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-cluster-autoscaler-irsa" })
}

data "aws_iam_policy_document" "cluster_autoscaler_permissions" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  statement {
    sid    = "Describe"
    effect = "Allow"
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeTags",
      "autoscaling:DescribeScalingActivities",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeLaunchTemplateVersions",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "Scale"
    effect = "Allow"
    actions = [
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  name        = "${var.project_name}-${var.environment}-cluster-autoscaler-policy"
  description = "Permissions required by the Kubernetes Cluster Autoscaler to scale EKS-managed Auto Scaling Groups."
  policy      = data.aws_iam_policy_document.cluster_autoscaler_permissions[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-cluster-autoscaler-policy" })
}

resource "aws_iam_role_policy_attachment" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  role       = aws_iam_role.cluster_autoscaler[0].name
  policy_arn = aws_iam_policy.cluster_autoscaler[0].arn
}

resource "helm_release" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = var.cluster_autoscaler_chart_version
  namespace  = "kube-system"

  set {
    name  = "autoDiscovery.clusterName"
    value = var.cluster_name
  }

  set {
    name  = "awsRegion"
    value = var.aws_region
  }

  set {
    name  = "rbac.serviceAccount.create"
    value = "true"
  }

  set {
    name  = "rbac.serviceAccount.name"
    value = "cluster-autoscaler"
  }

  set {
    name  = "rbac.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.cluster_autoscaler[0].arn
  }

  set {
    name  = "extraArgs.balance-similar-node-groups"
    value = "true"
  }

  set {
    name  = "extraArgs.skip-nodes-with-system-pods"
    value = "false"
  }

  # Ver el comentario en helm_release.external_secrets: este chart también
  # crea un Service, así que corre el mismo riesgo de carrera contra el
  # webhook del ALB Controller si Terraform los aplica en paralelo.
  depends_on = [
    aws_iam_role_policy_attachment.cluster_autoscaler,
    helm_release.aws_load_balancer_controller,
  ]
}

# ---------------------------------------------------------------------------
# External Secrets Operator
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "external_secrets_assume_role" {
  count = var.enable_external_secrets ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:external-secrets:external-secrets"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "external_secrets" {
  count = var.enable_external_secrets ? 1 : 0

  name               = "${var.project_name}-${var.environment}-external-secrets-irsa"
  assume_role_policy = data.aws_iam_policy_document.external_secrets_assume_role[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-external-secrets-irsa" })
}

data "aws_iam_policy_document" "external_secrets_permissions" {
  count = var.enable_external_secrets ? 1 : 0

  statement {
    sid    = "SecretsManagerRead"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:ListSecrets",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "KmsDecrypt"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "external_secrets" {
  count = var.enable_external_secrets ? 1 : 0

  name        = "${var.project_name}-${var.environment}-external-secrets-policy"
  description = "Permissions required by External Secrets Operator to read Secrets Manager entries and decrypt them via KMS."
  policy      = data.aws_iam_policy_document.external_secrets_permissions[0].json

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-external-secrets-policy" })
}

resource "aws_iam_role_policy_attachment" "external_secrets" {
  count = var.enable_external_secrets ? 1 : 0

  role       = aws_iam_role.external_secrets[0].name
  policy_arn = aws_iam_policy.external_secrets[0].arn
}

resource "helm_release" "external_secrets" {
  count = var.enable_external_secrets ? 1 : 0

  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  version          = var.external_secrets_chart_version
  namespace        = "external-secrets"
  create_namespace = true

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "external-secrets"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.external_secrets[0].arn
  }

  # Depende también del helm_release del ALB Controller, no solo de su IAM
  # role: el ALB Controller registra un webhook que intercepta la creación de
  # cualquier Service del clúster, y helm_release.aws_load_balancer_controller
  # solo tiene wait=true sobre SU PROPIO chart -- no bloquea a los demás
  # releases que Terraform aplicaría en paralelo. Sin esta dependencia
  # explícita, el Service que crea este chart puede llegar antes de que el
  # pod del ALB Controller tenga un endpoint vivo, y el webhook responde "no
  # endpoints available for service aws-load-balancer-webhook-service".
  depends_on = [
    aws_iam_role_policy_attachment.external_secrets,
    helm_release.aws_load_balancer_controller,
  ]
}

# ---------------------------------------------------------------------------
# Metrics Server (sin IRSA)
# ---------------------------------------------------------------------------

resource "helm_release" "metrics_server" {
  count = var.enable_metrics_server ? 1 : 0

  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server"
  chart      = "metrics-server"
  version    = var.metrics_server_chart_version
  namespace  = "kube-system"

  # Ver el comentario en helm_release.external_secrets: metrics-server
  # también crea un Service. En una corrida donde complete antes que el ALB
  # Controller esté listo puede chocar con el mismo webhook.
  depends_on = [helm_release.aws_load_balancer_controller]
}
