#!/bin/sh
set -eu

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn habit_control.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
