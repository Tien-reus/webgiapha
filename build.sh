#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate --noinput
if [ "$SEED_FORCE" = "1" ]; then
  python manage.py seed_initial_data --force
else
  python manage.py seed_initial_data
fi
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput || true
