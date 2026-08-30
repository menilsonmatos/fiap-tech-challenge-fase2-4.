variable "region" {
  description = "Região autorizada do AWS Academy Learner Lab"
  type        = string
  default     = "us-east-1"
}
variable "enable_monthly_batch" {
  description = "Ativa dia 1 as 06:00 UTC; habilitar somente apos publicar snapshot completo"
  type        = bool
  default     = false
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "project_name" {
  type    = string
  default = "fiap-alfabetizacao"
}
