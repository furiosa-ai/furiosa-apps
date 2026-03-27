#!/bin/bash
# Build frontend and copy to backend static folder

echo "Building frontend..."
npx vite build

echo "Copying build files to backend static folder..."
mkdir -p ../backend/static
cp -r dist/* ../backend/static/

echo "Frontend built and copied to backend/static/"
