#!/bin/bash
# Script to build the Docker image for AuDHD LifeCoach

# Set variables
IMAGE_NAME="audhd-lifecoach"
IMAGE_TAG="latest"

echo "Building Docker image $IMAGE_NAME:$IMAGE_TAG..."

# Build the Docker image
docker build -t $IMAGE_NAME:$IMAGE_TAG -f Dockerfile.simple ..

echo "Image built successfully: $IMAGE_NAME:$IMAGE_TAG"