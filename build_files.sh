#!/bin/bash


echo "Building the project"
python3.12 -m pip install -r requirements.txt

export PATH="/python312/bin:$PATH"


echo "Collect static files"
python3.12 manage.py collectstatic --noinput

echo "Check media files"
ls -l $MEDIA_ROOT