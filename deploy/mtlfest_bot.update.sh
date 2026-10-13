#!/bin/bash
# Update mtlfest_bot from prebuilt GHCR image and restart the service.
# Assumes `docker login ghcr.io` was done once on this machine.
set -e

SERVICE_FILE="mtlfest_bot.service"
IMAGE="ghcr.io/montelibero/mtlfest_bot:latest"

echo "Pulling fresh image: $IMAGE"
sudo docker pull "$IMAGE"

# Copy new service file if the unit definition changed
if ! sudo cmp -s "$SERVICE_FILE" /etc/systemd/system/mtlfest_bot.service; then
    echo "Service file changed - copying..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
fi

echo "Restarting service..."
sudo systemctl stop "$SERVICE_FILE"
sudo systemctl start "$SERVICE_FILE"

echo "Service status:"
sudo systemctl status "$SERVICE_FILE" --no-pager
