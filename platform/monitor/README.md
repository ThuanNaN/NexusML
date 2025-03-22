# Prometheus and Grafana

## Install Docker Plugin for Loki

Details: [Loki Docker Driver](https://grafana.com/docs/loki/latest/send-data/docker-driver/)

```bash
# CMD devices
docker plugin install grafana/loki-docker-driver:3.3.2-amd64 --alias loki --grant-all-permissions

# ARM devices
docker plugin install grafana/loki-docker-driver:3.3.2-arm64 --alias loki --grant-all-permissions
```
