variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where the security groups are created."
}

variable "vpc_cidr" {
  type        = string
  description = "VPC IPv4 CIDR block, used for intra-VPC egress/ingress rules."
}

variable "node_port_range_start" {
  type        = number
  description = "Lower bound of the Kubernetes NodePort range used by the ALB to reach EKS nodes."
  default     = 30000
}

variable "node_port_range_end" {
  type        = number
  description = "Upper bound of the Kubernetes NodePort range used by the ALB to reach EKS nodes."
  default     = 32767
}

# target_type = "ip" (infra/terraform/modules/alb, módulo usado por
# infra/k8s/platform/target-group-bindings.yaml) conecta el ALB DIRECTO a la
# IP del pod, en el puerto real de la app -- no en un NodePort. La regla
# eks_nodes_ingress_from_alb de más abajo solo abre el rango NodePort
# (30000-32767): confirmado contra el cluster real, los targets quedaban en
# estado unhealthy con reason Target.Timeout hasta agregar esta regla
# aparte. Puertos no contiguos (8080, 8000, ...) no caben en un solo
# from_port/to_port de aws_security_group_rule, así que es un puerto por
# entrada del set.
variable "app_ports" {
  type        = set(number)
  description = "Puertos reales de aplicación (no NodePort) a los que el ALB necesita llegar directo vía target_type=ip. Uno por cada valor distinto de `puerto` entre infra/k8s/values/*.yaml de los servicios en infra/terraform/environments/minimo/variables.tf (var.alb_routes)."
  default     = [8080, 8000]
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
