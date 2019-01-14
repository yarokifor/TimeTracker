## To quickly get this up and running

 cd to TimeTracker

 virtualenv -p python3 venv

 source venv/bin/activate

 (venv) pip install -r requirements.txt

 (create a hours/local_settings.py file with proper credentials -- see hours/local_settings.py.example)

 (venv) python ./manage.py makemigrations

 (venv) python ./manage.py migrate

 (venv) python ./manage.py runserver

## If you need to create a new superuser

 (venv) python ./manage.py createsuperuser

