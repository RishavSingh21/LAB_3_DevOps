provider "docker" {}

resource "docker_network" "lab3" {
  name   = var.network_name
  driver = "bridge"
}
