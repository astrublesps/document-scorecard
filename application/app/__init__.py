from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__, static_url_path='')
app.config.from_object('config')
db = SQLAlchemy(app)

# helpful logging script edited slightly from what is found on Miguel Grinberg's fantastic flask tutorial
# at http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

from app import views, models, scenarioList, compare, parser, output
