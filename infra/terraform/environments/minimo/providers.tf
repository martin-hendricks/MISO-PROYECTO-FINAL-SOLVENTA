provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# El Web ACL de WAF asociado a una distribución de CloudFront debe crearse en
# us-east-1 sin importar dónde viva el resto del stack. El módulo `edge` declara
# el alias aws.us_east_1 y esta es la configuración que lo satisface.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# El provider de Helm se autentica contra el clúster recién creado. El token se
# resuelve en cada invocación con `aws eks get-token`, de modo que no queda
# material de credenciales en el state.
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
    }
  }
}
