import re
from os import listdir
from os.path import isfile, join, dirname
from app import app

ALLOWED_EXTENSIONS = set(['xsd'])

class validate:


    @staticmethod
    def get_schema_list():
        schemas = []
        for f in listdir(app.config['SCHEMA_FOLDER']):
            if isfile(join(app.config['SCHEMA_FOLDER'], f)) and f.endswith('.xsd'):
                fname = re.sub('.xsd', '', str(f))
                schemas.append({'name': fname})
        return schemas

    @staticmethod
    def add_schema():
        print("add_schema")
        return null

    @staticmethod
    def delete_schema():
        print("delete_schema")
        return null
