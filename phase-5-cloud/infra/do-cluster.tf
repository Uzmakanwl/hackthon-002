terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/terraform-provider-digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  default = "todo-cluster"
}

variable "region" {
  default = "nyc1"
}

resource "digitalocean_kubernetes_cluster" "todo" {
  name    = var.cluster_name
  region  = var.region
  version = "1.28.2-do.0"

  node_pool {
    name       = "default-pool"
    size       = "s-2vcpu-4gb"
    node_count = 2
  }
}

output "cluster_id" {
  value = digitalocean_kubernetes_cluster.todo.id
}

output "endpoint" {
  value = digitalocean_kubernetes_cluster.todo.endpoint
}

output "kubeconfig" {
  value     = digitalocean_kubernetes_cluster.todo.kube_config[0].raw_config
  sensitive = true
}
