#!/bin/bash

function run_local() {
    echo "Running unit tests locally using Poetry..."
    cd docker_context
    poetry install
    poetry run pytest ../queue_listener/unit_tests.py -vvvv
    cd ..
}

function run_docker() {
    local tag=${1:-local}
    echo "Running integration and unit tests in Docker container..."
    if ! docker image inspect pdf-conversion:${tag} >/dev/null 2>&1; then
        echo "Image not found locally, building..."
        if docker buildx version >/dev/null 2>&1; then
            docker buildx build --load -t pdf-conversion:${tag} .
        else
            docker build -t pdf-conversion:${tag} .
        fi
    fi
    docker run --rm --user root pdf-conversion:${tag} /etc/poetry/bin/poetry run pytest queue_listener/ -vvvv
}

case "$1" in
    "local")
        run_local
        ;;
    "docker")
        run_docker "${2:-local}"  # Pass optional tag parameter
        ;;
    *)
        echo "Usage: ./run-tests.sh [local|docker]"
        echo "  local  - Run unit tests using local Poetry installation"
        echo "  docker - Run integration and unit tests in Docker container (matches CI environment)"
        exit 1
        ;;
esac
