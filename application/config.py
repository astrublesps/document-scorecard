import os
basedir = os.path.abspath(os.path.dirname(__file__))

#configuration file for the app. This is where the upload folder and database are set globally.


#-------------------------------------------------------------------------------
#This is for the use on the ubuntu server
# UPLOAD_FOLDER = 'ALL_UPLOADS'
# SQLALCHEMY_DATABASE_URI = 'postgresql:///scorecard'
# SQLALCHEMY_BINDS = {'usagedb': 'postgresql:///appusage',}
# APP_NAME = 'DSC'
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#This is for the use on a local machine
UPLOAD_FOLDER = 'C:/Uploads'
if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
#-------------------------------------------------------------------------------

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SECRET_KEY = '0Zr98j/3yX R~XHH!jmN]LWX/,?RTA'
