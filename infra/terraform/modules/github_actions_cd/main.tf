# CI/CD desde GitHub Actions hacia AWS, sin access keys de larga duración.
#
# GitHub Actions firma un JSON Web Token por cada ejecución de workflow
# (cuando el workflow declara `permissions.id-token: write`). Este módulo
# registra ese emisor como un proveedor OIDC de IAM y crea un rol que solo
# ese JWT puede asumir -- y solo cuando el JWT dice que viene de este
# repositorio, en una de las ramas listadas en var.github_branches. Ninguna
# otra rama, fork o repositorio puede autenticarse como este rol.
#
# El rol resultante es exactamente lo que necesita el workflow de
# despliegue (.github/workflows/deploy.yml, aún no creado): empujar
# imágenes a los repositorios ECR existentes y resolver las credenciales
# de kubectl contra el clúster EKS existente. No crea ni modifica
# Deployments de Kubernetes -- eso lo hace `helm upgrade` desde el
# workflow, no Terraform (ver infra/k8s/README.md, "Frontera
# Terraform/Kubernetes").

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  role_name = "${var.project_name}-${var.environment}-github-actions-cd"

  # El JWT de GitHub Actions trae el claim `sub` con esta forma exacta para
  # un push/merge en una rama (no un PR, no un tag, no un environment):
  # repo:<org>/<repo>:ref:refs/heads/<rama>.
  subject_claims = [
    for branch in var.github_branches :
    "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${branch}"
  ]
}

# ---------------------------------------------------------------------------
# Proveedor OIDC — el emisor de tokens de GitHub Actions
# ---------------------------------------------------------------------------

data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-github-actions-oidc" })
}

# ---------------------------------------------------------------------------
# Rol asumible solo por workflows de este repositorio, en estas ramas
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.subject_claims
    }
  }
}

resource "aws_iam_role" "github_actions_cd" {
  name               = local.role_name
  description        = "Asumible solo por GitHub Actions del repo ${var.github_org}/${var.github_repo}, ramas: ${join(", ", var.github_branches)}."
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = merge(local.common_tags, { Name = local.role_name })
}

# ---------------------------------------------------------------------------
# Permisos: push/pull de imágenes a los repositorios ECR existentes
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid       = "AuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"] # ecr:GetAuthorizationToken no admite scoping a un repositorio.
  }

  statement {
    sid    = "PushPullImages"
    effect = "Allow"

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
    ]

    resources = var.ecr_repository_arns
  }
}

resource "aws_iam_policy" "ecr_push" {
  name        = "${local.role_name}-ecr"
  description = "Push/pull de imágenes a los repositorios ECR de los componentes desplegables de Solventa."
  policy      = data.aws_iam_policy_document.ecr_push.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecr_push" {
  role       = aws_iam_role.github_actions_cd.name
  policy_arn = aws_iam_policy.ecr_push.arn
}

# ---------------------------------------------------------------------------
# Permisos: resolver credenciales de kubectl contra el clúster EKS
# ---------------------------------------------------------------------------
#
# Solo cubre `aws eks update-kubeconfig` (describir el clúster para armar el
# kubeconfig). La autorización real dentro del clúster -- qué puede hacer
# este rol una vez autenticado contra la API de Kubernetes -- la concede el
# access entry de EKS, no esta política de IAM. Ver outputs.tf.

data "aws_iam_policy_document" "eks_describe" {
  statement {
    sid       = "DescribeCluster"
    effect    = "Allow"
    actions   = ["eks:DescribeCluster"]
    resources = [var.eks_cluster_arn]
  }
}

resource "aws_iam_policy" "eks_describe" {
  name        = "${local.role_name}-eks-describe"
  description = "Permite resolver el kubeconfig del clúster EKS de Solventa desde el workflow de despliegue."
  policy      = data.aws_iam_policy_document.eks_describe.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "eks_describe" {
  role       = aws_iam_role.github_actions_cd.name
  policy_arn = aws_iam_policy.eks_describe.arn
}

# ---------------------------------------------------------------------------
# Access entry: autorización dentro del clúster (API de Kubernetes)
# ---------------------------------------------------------------------------
#
# Lo anterior permite resolver el kubeconfig; esto autoriza lo que el rol
# puede hacer una vez autenticado contra la API de Kubernetes.
#
# Scope a nivel de CLÚSTER (no acotado al namespace `solventa`) a propósito:
# el mismo workflow de despliegue también crea el namespace `solventa` y el
# ClusterSecretStore si todavía no existen (paso de bootstrap idempotente en
# deploy.yml) -- ambos son recursos a nivel de clúster, no de namespace, así
# que un scope "namespace" no alcanzaría para crearlos. Decisión consciente
# de simplicidad operativa sobre mínimo privilegio estricto para este
# ambiente: un solo rol para todo el workflow, en vez de dos roles (uno de
# bootstrap cluster-admin y otro de deploy acotado a namespace) que se
# asumen en pasos distintos del mismo job.
#
# AmazonEKSEditPolicy: lee/escribe recursos de aplicación (Deployments,
# Services, ConfigMaps, HPA, Namespaces, etc.), pero no toca RBAC
# (Roles/ClusterRoles/bindings) ni borra el propio clúster.

resource "aws_eks_access_entry" "github_actions_cd" {
  cluster_name  = var.eks_cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  type          = "STANDARD"

  tags = local.common_tags
}

resource "aws_eks_access_policy_association" "github_actions_cd" {
  cluster_name  = var.eks_cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.github_actions_cd]
}
