from flask import Flask
import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

contains = db.Table('contains',
                    db.Column('esp_id', db.Integer, db.ForeignKey('ESP.id')),
                    db.Column('scenario_id', db.Integer, db.ForeignKey('scenario.id'))
                    )

esp_groups = db.Table('esp_groups',
                      db.Column('esp_me_id', db.Integer, db.ForeignKey('ESP.id')),
                      db.Column('esp_equal_to_id', db.Integer, db.ForeignKey('ESP.id'))
                      )

qual_children = db.Table('qual_children',
                         db.Column('qual_esp_id', db.Integer, db.ForeignKey('ESP.id')),
                         db.Column('qual_child_esp_id', db.Integer, db.ForeignKey('ESP.id'))
                         )


class ESP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    data = db.Column(db.String(300))
    xpath = db.Column(db.String(500), index=True)
    is_qual = db.Column(db.Boolean)
    equal_elements = db.relationship('ESP',
                                     secondary = esp_groups,
                                     primaryjoin=(esp_groups.c.esp_me_id == id),
                                     secondaryjoin=(esp_groups.c.esp_equal_to_id == id),
                                     backref = db.backref('esp_groups', lazy = 'dynamic'),
                                     lazy='dynamic')
    children =  db.relationship('ESP', secondary = qual_children,
                               primaryjoin=(qual_children.c.qual_esp_id == id),
                               secondaryjoin=(qual_children.c.qual_child_esp_id == id),
                               backref=db.backref('qual_children', lazy = 'dynamic'),
                               lazy='dynamic')


class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(65), index=True, unique=True)
    schema = db.Column(db.String(100))
    description = db.Column(db.String(200))
    doctype = db.Column(db.String(55))
    fulfillmenttype = db.Column(db.String(100))
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    esps = db.relationship('ESP', secondary=contains, primaryjoin=(contains.c.scenario_id == id),
                           backref=db.backref('scenarios', lazy='dynamic'))


class Appinfo(db.Model):
    __bind_key__ = 'usagedb'
    __tablename__ = 'appinfo'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100), nullable=False)
    starttime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    processtime = db.Column(db.Float(15), nullable=False)
    error = db.Column(db.Boolean)
    misc = db.Column(db.String(200), nullable=True)
    fn_app = db.Column(db.Integer, db.ForeignKey('apps.id'),
                       nullable=False)


class Apps(db.Model):
    __bind_key__ = 'usagedb'
    __tablename__ = 'apps'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True)
    appinfo = db.relationship('Appinfo', backref='App',
                              order_by='Appinfo.id', lazy='dynamic',
                              cascade='all, delete, delete-orphan')


if __name__ == '__main__':
    manager.run()