#!/bin/sh
# Day 3 — publish the Day 2 image to Docker Hub.
#
# Usage:
#   ./scripts/publish.sh <docker-hub-username> [tag]
#   ./scripts/publish.sh smia-sajid day2
#
# You must already be logged in: run `docker login` first and use your
# own Docker Hub username and password / token. Never put a password
# in this script or in the repo.
set -e

USER_NAME="${1:-}"
TAG="${2:-day2}"

if [ -z "$USER_NAME" ]; then
  echo "Usage: $0 <docker-hub-username> [tag]" >&2
  exit 1
fi

IMAGE="$USER_NAME/my-app:$TAG"

echo "Building my-app:$TAG ..."
docker build -t "my-app:$TAG" .

echo "Tagging as $IMAGE ..."
docker tag "my-app:$TAG" "$IMAGE"

echo "Pushing $IMAGE ..."
docker push "$IMAGE"

echo "Done. Anyone can now run it with:"
echo "  docker pull $IMAGE"
echo "  docker run -p 8000:8000 $IMAGE"
