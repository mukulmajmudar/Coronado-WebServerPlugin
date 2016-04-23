#!/bin/bash
set -x
docker build -t $USER/coronado-webserverplugin .
docker run --rm --entrypoint=pylint $USER/coronado-webserverplugin WebServerPlugin
