variable "region" {
  description = "Região autorizada do AWS Academy Learner Lab"
  type        = string
  default     = "us-east-1"
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "project_name" {
  type    = string
  default = "fiap-alfabetizacao"
}
