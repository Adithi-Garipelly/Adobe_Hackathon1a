#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t pdf-heading-extractor .

# Run the container with input/output volume mounts
echo "Running container..."
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  --network none \
  pdf-heading-extractor

echo "Processing complete! Check the output directory for results." 