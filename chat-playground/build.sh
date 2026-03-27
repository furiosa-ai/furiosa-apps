#!/bin/bash

# Build script for OSS Demo
# Builds frontend with Vite and copies to backend static directory

echo "🔨 Building frontend..."

# Navigate to frontend directory
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Build frontend with Vite
echo "🏗️  Running Vite build..."
npm run build

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend build completed!"

# Navigate back to root
cd ..

# Create backend static directory if it doesn't exist
echo "📁 Creating backend static directory..."
mkdir -p backend/static

# Copy built files to backend static directory
echo "📋 Copying built files to backend/static..."
cp -r frontend/dist/* backend/static/

# Check if copy was successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to copy files to backend static directory!"
    exit 1
fi

echo "✅ Build and integration completed successfully!"
echo "🚀 Backend can now serve the frontend from /backend/static/"
