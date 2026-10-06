output "spa_bucket_name" {
  value       = aws_s3_bucket.spa.id
  description = "Name of the S3 bucket hosting the Angular SPA."
}

output "spa_bucket_arn" {
  value       = aws_s3_bucket.spa.arn
  description = "ARN of the S3 bucket hosting the Angular SPA."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.spa.id
  description = "ID of the CloudFront distribution in front of the SPA bucket."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.spa.domain_name
  description = "CloudFront domain name (e.g. dxxxxxxx.cloudfront.net) serving the SPA."
}

output "waf_web_acl_arn" {
  value       = aws_wafv2_web_acl.cloudfront.arn
  description = "ARN of the WAF Web ACL attached to the CloudFront distribution."
}

output "waf_web_acl_id" {
  value       = aws_wafv2_web_acl.cloudfront.id
  description = "ID of the WAF Web ACL attached to the CloudFront distribution."
}

output "api_gateway_id" {
  value       = aws_apigatewayv2_api.this.id
  description = "ID of the HTTP API Gateway (entry point for distribution partners)."
}

output "api_gateway_endpoint" {
  value       = aws_apigatewayv2_stage.default.invoke_url
  description = "Invoke URL of the API Gateway default stage."
}

output "vpc_link_id" {
  value       = aws_apigatewayv2_vpc_link.alb.id
  description = "ID of the VPC Link connecting the API Gateway to the internal ALB (EC-SEG-07)."
}
