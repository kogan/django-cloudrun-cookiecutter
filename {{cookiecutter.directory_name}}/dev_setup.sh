#!/usr/bin/env bash

#!/bin/bash
set -e

echo "Warning, this will recreate your current docker environment, including deleting the DB volume"
read -p "Are you sure you want to proceed (y/n)? " YESNO

if [ "$YESNO" != 'y' ]
then
    echo "Aborting"
    exit 1
fi

if [ ! -f ".env" ] ; then
    # docker compose won't startup unless an env file is there
    touch ".env"
fi

# Take down containers and remove volumes
docker-compose down -v

# kill any running containers
docker-compose kill

# clean up
docker-compose rm -fv

# todo:
# echo "fetching fixtures..."
# ./bin/fetch_dumps.py

docker-compose up -d db
sleep 3

echo "migrating..."
docker-compose run --rm django python -Wall manage.py migrate

docker-compose up -d django

echo "done."
echo "server is running at http://localhost:8317/admin/"
