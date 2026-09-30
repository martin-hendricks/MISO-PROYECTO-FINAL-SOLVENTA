terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.us_east_1]
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }
}

# NOTE: aws_wafv2_web_acl for a CloudFront distribution must be created in
# us-east-1 regardless of where the rest of the stack lives. This module
# declares the aws.us_east_1 provider alias above; the caller (the
# environments/minimo composition) MUST pass a provider block aliased to
# us-east-1, e.g.:
#
#   provider "aws" {
#     alias  = "us_east_1"
#     region = "us-east-1"
#   }
#
#   module "edge" {
#     source = "../../modules/edge"
#     providers = {
#       aws           = aws
#       aws.us_east_1 = aws.us_east_1
#     }
#     ...
#   }
