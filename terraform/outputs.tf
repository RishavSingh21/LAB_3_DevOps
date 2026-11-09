output "network_name" {
  description = "Name of the Docker network used by the Compose stack."
  value       = docker_network.lab3.name
}
