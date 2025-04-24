@echo off
REM Script to build the Docker image for AuDHD LifeCoach

REM Set variables
SET IMAGE_NAME=audhd-lifecoach
SET IMAGE_TAG=latest

echo Building Docker image %IMAGE_NAME%:%IMAGE_TAG%...

REM Build the Docker image from the project root
cd ..
docker build -t %IMAGE_NAME%:%IMAGE_TAG% -f Dockerfile.simple .

echo Image built successfully: %IMAGE_NAME%:%IMAGE_TAG%
pause