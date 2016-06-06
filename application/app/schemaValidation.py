import re
import os
from os import listdir
from os.path import isfile, join, dirname
from app import app, schemaCreation
from werkzeug import secure_filename

class validate:

    SCHEMA_EXTENSIONS = ['xsd']

    @staticmethod
    def schema_allowed(filename):
        return '.' in filename and filename.rsplit('.', 1)[1] in validate.SCHEMA_EXTENSIONS

    @staticmethod
    def get_schema_list():
        schemas = []
        for f in listdir(app.config['SCHEMA_FOLDER']):
            if isfile(join(app.config['SCHEMA_FOLDER'], f)) and f.endswith('.xsd'):
                name = re.sub('.xsd', '', str(f))
                schemas.append({'name': name})
        return schemas

    @staticmethod
    def add_schema(file, schema_name):
        print("add_schema")
        if validate.schema_allowed(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.isfile(app.config['SCHEMA_FOLDER'] + '/' + schema_name + '.xsd'):
                file.save(os.path.join(app.config['SCHEMA_FOLDER'], filename))
                os.rename(app.config['SCHEMA_FOLDER'] + '/' + filename,app.config['SCHEMA_FOLDER'] + '/' + schema_name + '.xsd')
                schemaCreation.create.configure_xsd(app.config['SCHEMA_FOLDER'] + '/' + schema_name + '.xsd')
            else:
                return False,  'A schema with name %s already exists.' % schema_name
        else:
            return False, 'File uploaded must be a valid schema with file extension of .xsd.'

        return True, ''

    @staticmethod
    def delete_schema(filename):
        print("delete_schema")
        if os.path.isfile(app.config['SCHEMA_FOLDER'] + '/' + filename + '.xsd'):
            os.remove(app.config['SCHEMA_FOLDER'] + '/' + filename + '.xsd')
        return True, ''
