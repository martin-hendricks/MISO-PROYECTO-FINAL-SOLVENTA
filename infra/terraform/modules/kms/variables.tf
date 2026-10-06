variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "deletion_window_in_days" {
  type        = number
  description = "Waiting period (in days) before a key is deleted after being scheduled for deletion. Low by default so the environment stays destructible (HU-78)."
  default     = 7
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
