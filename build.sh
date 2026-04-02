#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Migrate database
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input