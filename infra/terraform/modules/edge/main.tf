locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  bucket_suffix = length(var.bucket_suffix) > 0 ? var.bucket_suffix : random_id.spa_bucket_suffix.hex
  spa_bucket_name = lower(
    "${var.project_name}-${var.environment}-spa-${local.bucket_suffix}"
  )
}

resource "random_id" "spa_bucket_suffix" {
  byte_length = 4
}

# =============================================================================
# a) S3 — hosting privado de la SPA Angular, servido vía CloudFront + OAC
# =============================================================================

resource "aws_s3_bucket" "spa" {
  bucket        = local.spa_bucket_name
  force_destroy = var.spa_bucket_force_destroy

  tags = merge(local.common_tags, { Name = local.spa_bucket_name })
}

resource "aws_s3_bucket_versioning" "spa" {
  bucket = aws_s3_bucket.spa.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "spa" {
  bucket = aws_s3_bucket.spa.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "spa" {
  bucket = aws_s3_bucket.spa.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Origin Access Control: only this CloudFront distribution may read the bucket.
resource "aws_cloudfront_origin_access_control" "spa" {
  name                              = "${var.project_name}-${var.environment}-spa-oac"
  description                       = "OAC for the Solventa Angular SPA bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "spa_bucket" {
  statement {
    sid    = "AllowCloudFrontServicePrincipalReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.spa.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.spa.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "spa" {
  bucket = aws_s3_bucket.spa.id
  policy = data.aws_iam_policy_document.spa_bucket.json
}

# =============================================================================
# b) CloudFront — distribución delante de la SPA, con OAC (no OAI legacy)
# =============================================================================

resource "aws_cloudfront_distribution" "spa" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class
  web_acl_id          = aws_wafv2_web_acl.cloudfront.arn
  comment             = "${var.project_name}-${var.environment} Angular SPA"

  origin {
    domain_name              = aws_s3_bucket.spa.bucket_regional_domain_name
    origin_id                = "spa-s3-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.spa.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "spa-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # SPA routing: unknown paths (403/404 from S3) fall back to index.html.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-spa-cf" })
}

# =============================================================================
# c) WAF — Web ACL para CloudFront (scope CLOUDFRONT vive en us-east-1)
# =============================================================================

resource "aws_wafv2_web_acl" "cloudfront" {
  provider = aws.us_east_1

  name        = "${var.project_name}-${var.environment}-cf-waf"
  description = "Web ACL for the Solventa CloudFront distribution (SPA + edge)"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # --- AWS managed rule groups ---

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 0

    override_action {
      dynamic "count" {
        for_each = var.waf_managed_rules_action == "count" ? [1] : []
        content {}
      }
      dynamic "none" {
        for_each = var.waf_managed_rules_action == "block" ? [1] : []
        content {}
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${var.environment}-common-rule-set"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 1

    override_action {
      dynamic "count" {
        for_each = var.waf_managed_rules_action == "count" ? [1] : []
        content {}
      }
      dynamic "none" {
        for_each = var.waf_managed_rules_action == "block" ? [1] : []
        content {}
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${var.environment}-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 2

    override_action {
      dynamic "count" {
        for_each = var.waf_managed_rules_action == "count" ? [1] : []
        content {}
      }
      dynamic "none" {
        for_each = var.waf_managed_rules_action == "block" ? [1] : []
        content {}
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${var.environment}-sqli-rule-set"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 3

    override_action {
      dynamic "count" {
        for_each = var.waf_managed_rules_action == "count" ? [1] : []
        content {}
      }
      dynamic "none" {
        for_each = var.waf_managed_rules_action == "block" ? [1] : []
        content {}
      }
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${var.environment}-ip-reputation"
      sampled_requests_enabled   = true
    }
  }

  # --- Rate limiting: per-IP request cap ---

  rule {
    name     = "RateLimitPerIp"
    priority = 4

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.project_name}-${var.environment}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-cf-waf"
    sampled_requests_enabled   = true
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-cf-waf" })
}

# =============================================================================
# d) API Gateway — HTTP API, punto de entrada de socios de distribución,
#    integración HTTP_PROXY hacia el ALB
# =============================================================================

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_allow_origins
    allow_methods = var.cors_allow_methods
    allow_headers = var.cors_allow_headers
    max_age       = var.cors_max_age
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-api" })
}

# VPC Link privado (EC-SEG-07): el único camino que el API Gateway tiene
# hacia el ALB interno. Antes la integración era HTTP_PROXY directo a la IP
# pública del ALB, lo que dejaba un segundo camino de entrada que no pasaba
# por este Gateway ni por su WAF/throttling.
resource "aws_apigatewayv2_vpc_link" "alb" {
  name               = "${var.project_name}-${var.environment}-apigw-vpclink"
  subnet_ids         = var.vpc_link_subnet_ids
  security_group_ids = var.vpc_link_security_group_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-apigw-vpclink" })
}

resource "aws_apigatewayv2_integration" "alb_proxy" {
  api_id             = aws_apigatewayv2_api.this.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = var.alb_listener_arn

  connection_type = "VPC_LINK"
  connection_id   = aws_apigatewayv2_vpc_link.alb.id

  payload_format_version = "1.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.alb_proxy.id}"
}

resource "aws_cloudwatch_log_group" "apigw_access_logs" {
  name              = "/apigw/${var.project_name}-${var.environment}"
  retention_in_days = var.apigw_log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-apigw-logs" })
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw_access_logs.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      ip               = "$context.identity.sourceIp"
      requestTime      = "$context.requestTime"
      httpMethod       = "$context.httpMethod"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      protocol         = "$context.protocol"
      responseLength   = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.apigw_throttling_burst_limit
    throttling_rate_limit  = var.apigw_throttling_rate_limit
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-apigw-stage" })
}
