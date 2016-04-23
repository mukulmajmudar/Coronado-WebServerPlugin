#!/bin/bash
set -x
docker build -t $USER/coronado-webserverplugin .
mkdir -p dist
docker run --rm \
    -e USERID=$EUID \
    -v `pwd`/dist:/root/WebServerPlugin/dist \
    $USER/coronado-webserverplugin
