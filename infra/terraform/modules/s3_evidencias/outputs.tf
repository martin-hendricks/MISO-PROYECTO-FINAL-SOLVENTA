output "bucket_id" {
  value       = aws_s3_bucket.this.id
  description = "Name/ID of the claim evidence S3 bucket."
}

output "bucket_arn" {
  value       = aws_s3_bucket.this.arn
  description = "ARN of the claim evidence S3 bucket."
}

output "bucket_domain_name" {
  value       = aws_s3_bucket.this.bucket_domain_name
  description = "Global domain name of the bucket."
}

output "bucket_regional_domain_name" {
  value       = aws_s3_bucket.this.bucket_regional_domain_name
  description = "Region-specific domain name of the bucket, used by clients uploading directly (e.g. the mobile app)."
}
