# CI/CD desde GitHub Actions hacia AWS, sin access keys de larga duración.
#
# GitHub Actions firma un JSON Web Token por cada ejecución de workflow
# (cuando el workflow declara `permissions.id-token: write`). Este módulo
# registra ese emisor como un proveedor OIDC de IAM y crea un rol que solo
# ese JWT puede asumir -- y solo cuando el JWT dice que viene de este
# repositorio, en uno de los GitHub Environments listados en
# var.github_environments. Ningún otro repositorio, fork o job sin
# environment puede autenticarse como este rol.
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

  # Cuando un job de GitHub Actions declara `environment: <nombre>`, el
  # claim `sub` del JWT deja de tener la forma basada en rama
  # (repo:<org>/<repo>:ref:refs/heads/<rama>) y pasa a esta otra:
  # repo:<org>/<repo>:environment:<nombre>. deploy.yml declara
  # `environment: desarrollo|produccion` en sus jobs, así que la condición
  # debe matchear por environment, no por rama -- usar la forma basada en
  # rama aquí (como en un primer intento) hace que AWS rechace el
  # AssumeRoleWithWebIdentity con "Not authorized" aunque el ARN del rol y
  # el push sean correctos.
  #
  # Además, confirmado en CloudTrail, el sub real que GitHub envía incluye
  # los IDs numéricos de la organización y del repositorio como sufijo del
  # nombre (repo:<org>@<org_id>/<repo>@<repo_id>:environment:<nombre>), no
  # solo repo:<org>/<repo>:environment:<nombre>. Esos IDs no son
  # predecibles de antemano ni estables si el repo se transfiere, así que
  # se toleran con un wildcard (StringLike) en vez de hardcodearlos. El "@"
  # es literal: exige que el nombre de org/repo termine exactamente ahí
  # antes del wildcard, para que "martin-hendricks" no matchee como prefijo
  # de otra organización con un nombre más largo.
  subject_claims = [
    for env in var.github_environments :
    "repo:${var.github_org}@*/${var.github_repo}@*:environment:${env}"
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
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.subject_claims
    }
  }
}

resource "aws_iam_role" "github_actions_cd" {
  name               = local.role_name
  description        = "Asumible solo por GitHub Actions del repo ${var.github_org}/${var.github_repo}, environments: ${join(", ", var.github_environments)}."
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
# AmazonEKSClusterAdminPolicy (no AmazonEKSEditPolicy): el bootstrap de
# deploy.yml aplica infra/k8s/platform/clustersecretstore.yaml, un CRD de
# External Secrets Operator (external-secrets.io/v1beta1), no un recurso
# core de Kubernetes. AmazonEKSEditPolicy solo cubre recursos de aplicación
# nativos (Deployments, Services, ConfigMaps, HPA, Namespaces...); no
# conoce CRDs de terceros, así que un `kubectl apply` sobre
# ClusterSecretStore fallaba con "forbidden" aunque el AssumeRoleWithWebIdentity
# ya funcionara. ClusterAdminPolicy (sin llegar a AdminPolicy, que además
# puede modificar RBAC de otros principals) cubre cualquier CRD presente o
# futuro sin tener que enumerar API groups uno por uno -- misma decisión de
# simplicidad operativa sobre mínimo privilegio estricto que ya se tomó
# para var.eks_cluster_name arriba y para el usuario que aplica Terraform
# (ver aws_eks_access_entry.terraform_admin en modules/eks/main.tf).

resource "aws_eks_access_entry" "github_actions_cd" {
  cluster_name  = var.eks_cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  type          = "STANDARD"

  tags = local.common_tags
}

resource "aws_eks_access_policy_association" "github_actions_cd" {
  cluster_name  = var.eks_cluster_name
  principal_arn = aws_iam_role.github_actions_cd.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.github_actions_cd]
}
