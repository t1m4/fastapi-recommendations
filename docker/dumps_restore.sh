#!/bin/bash

echo "Preparing recommendation database..."

filename=".dumps/recommendations.sql"
if [ ! -f $filename ]
then
    echo "$filename doesn't exists, recommendations database will be empty.";
    exit 0
fi

psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS recommendations;"
psql -U "$POSTGRES_USER" -c "CREATE DATABASE recommendations;"

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f $filename
