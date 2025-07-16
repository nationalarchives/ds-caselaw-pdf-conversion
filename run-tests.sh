#!/bin/bash

function run_local() {
    echo "Running unit tests locally using Poetry..."
    cd docker_context
    poetry install
    poetry run pytest ../queue_listener/unit_tests.py -vvvv
    cd ..
}

function run_docker() {
    echo "Running integration and unit tests in Docker container..."
    docker build -t pdf-conversion:local .
    docker run --rm --user root pdf-conversion:local /etc/poetry/bin/poetry run pytest queue_listener/ -vvvv
}

case "$1" in
    "local")
        run_local
        ;;
    "docker")
        run_docker
        ;;
    *)
        echo "Usage: ./run-tests.sh [local|docker]"
        echo "  local  - Run unit tests using local Poetry installation"
        echo "  docker - Run integration and unit tests in Docker container (matches CI environment)"
        exit 1
        ;;
esac
