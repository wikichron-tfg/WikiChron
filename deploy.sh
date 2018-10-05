#!/bin/sh
(git pull origin master && pkill -HUP gunicorn) || (gunicorn production_app:wikichron -c gunicorn_config.py)
