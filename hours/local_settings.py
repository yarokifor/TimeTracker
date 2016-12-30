import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

main_settings = BASE_DIR+'/hours/settings.py'

exec(compile(open(main_settings).read(),main_settings,'exec'))

SECRET_KEY = "" 

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1",]

