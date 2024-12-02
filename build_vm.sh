#!/usr/bin/env bash

# check tag given by user
if [ -z $1 ];
then echo "user should supply a tag for the docker image" 
echo "e.g.: bash build.sh <tag>"
exit 1
fi

echo "building image celsiuspro/nccs_vm:${1}"
docker build --rm \
    -t celsiuspro/nccs_vm:${1} \
    --platform=linux/amd64 \
    -f Dockerfile.vmrun \
    .
