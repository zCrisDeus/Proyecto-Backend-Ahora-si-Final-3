from .test_settings import *
# Dedicated disposable PostgreSQL cluster for tests only. Never use production here.
DATABASES={'default':{
    'ENGINE':'django.db.backends.postgresql',
    'NAME':'postgres',
    'USER':'petcare_test',
    'HOST':'127.0.0.1',
    'PORT':os.environ.get('PETCARE_TEST_PG_PORT','55439'),
    'TEST':{'NAME':'test_petcare_features'},
}}
