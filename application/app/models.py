from flask import Flask
import datetime
from sqlalchemy import asc, func
from sqlalchemy.sql import exists
from sqlalchemy.ext.associationproxy import association_proxy
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

# contains is relationship table for the many-to-many relationship between ESPs and Scenarios
# it has foreign keys for the esps and for the scenarios
contains = db.Table('contains',
                    db.Column('esp_id', db.Integer, db.ForeignKey('ESP.id')),
                    db.Column('scenario_id', db.Integer, db.ForeignKey('scenario.id'))
                    )


# ESP is the table for the esps. It has id (used for the database), score, xpath, and data columns
# For esps, the combination of xpath, score, and data is unique in the table. This is for efficiency, since there are
# only 5 possible scores, there is likely to be a lot of overlap in the esps that scenarios contain.
class ESP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    data = db.Column(db.String(300))
    xpath = db.Column(db.String(500), index=True)

    def __init__(self, xpath, score, data):
        self.score = score
        self.xpath = xpath
        self.data = data

    # Check to see whether an esp is already in the database
    @staticmethod
    def esp_exists(xpath, score, data):
        return ESP.query.filter(ESP.xpath == xpath, ESP.score == score,
                                ESP.data == data).first() is not None

    # Return an esp given its score and xpath
    @staticmethod
    def get_esp(xpath, score, data):
        return ESP.query.filter(ESP.xpath == xpath, ESP.score == score, ESP.data == data).first()

    # remove a particular esp from the database
    def delete_esp(self, name):
        esp = ESP.query.filter_by(self.name == name)
        db.session.delete(esp)
        db.session.commit()

    # ToString method for an esp
    def __repr__(self):
        return '<ESP %r>' % (str(self.id) + " " + self.xpath + " " + str(self.score) + " " + str(self.data))

    def serialize(self):
        return {'id': self.id,
                'xpath': self.xpath,
                'score': self.score,
                'data': self.data
                }


# Scenario is the table for scenarios. Each scenario has a unique name, non-unique description, and a relationship with
# zero or more esps through the contains table.
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

    def __init__(self, name, schema, description, doctype, fulfillmenttype):
        if not Scenario.check_exists(name):
            self.name = name
            self.schema = schema
            self.description = description
            self.doctype = doctype
            self.fulfillmenttype = fulfillmenttype
            self.date_created = Scenario.get_current_time()
            self.date_updated = Scenario.get_current_time()

    # Check to see if a scenario exists, given its name
    @staticmethod
    def check_exists(check_name):
        return Scenario.query.filter_by(name=check_name).first() is not None

    # Get a particular scenario from the database, given its name
    @staticmethod
    def get_scenario(scen_name):
        if Scenario.check_exists(scen_name):
            return Scenario.query.filter_by(name=scen_name).first()

    # Return esps related to a specific scenario as esps, or objects, so that they can be manipulated
    # Used in the Compare and ScenarioList classes
    def get_esps(self):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id).order_by(asc(ESP.xpath)).all()

    # Return a particular esp related to a specific scenario
    def get_single_esp_for_scen(self, xpath, score, data):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id, ESP.xpath == xpath,
                                               ESP.score == score, ESP.data == data).first()

    # Return a specific ESP for this scenario, but without checking score (since there should only be one score for any given
    # xpath/data combo, e.g. AddressTypeCode where data is ST can only have one score per scenario. Used in ScenarioList.build_scenario()
    def get_single_esp_no_score(self, g_xpath, g_data):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id, ESP.xpath == g_xpath,
                                               ESP.data == g_data).first()

    # Return esps related to a specific scenario as a list, so that they can be read
    # Used in the ScenarioList class
    def get_esps_as_list(self):
        all_esps = ESP.query.join(contains).filter(contains.c.scenario_id == self.id).order_by(asc(ESP.xpath)).all()
        list_of_esps = []
        for esp in all_esps:
            x = {'xpath': esp.xpath, 'data': esp.data, 'score': esp.score}
            list_of_esps.append(x)
        return list_of_esps

    # Method to check whether a scenario exists before creating it, create it, and commit it
    @staticmethod
    def create_scenario(name, schema, new_description, doctype, fulfillmenttype):
        if not Scenario.check_exists(name):
            scen = Scenario(name, schema, new_description, doctype, fulfillmenttype)
            db.session.add(scen)
            db.session.commit()
            return scen
        else:
            return None

    # Method to check that a scenario exists, delete, and commit the change
    @staticmethod
    def delete_scenario(name):
        if Scenario.check_exists(name):
            del_scen = Scenario.get_scenario(name)
            print(del_scen.id)
            print(ESP.query.join(contains).all())
            esps_to_delete = ESP.query.join(contains).filter(contains.c.scenario_id == del_scen.id).all()
            for esp in esps_to_delete:
                print("delete esp" + str(esp))
                del_scen.remove_esp(esp)
                # db.session.delete(esp)
            db.session.delete(del_scen)
            db.session.commit()
            # cleanup_esps = ESP.query.outerjoin(contains).filter(contains.c.scenario_id is None).all()
            # # for esp in cleanup_esps:
            #     # print("delete esp" + str(esp))
            #     # db.session.delete(esp)
            # print(ESP.query.join(contains).all())
            return True
        else:
            return False

    def edit(self, name, schema, description, doctype, fulfillmenttype):
        self.name = name
        self.schema = schema
        self.description = description
        self.doctype = doctype
        self.fulfillmenttype = fulfillmenttype
        self.date_updated = Scenario.get_current_time()
        db.session.commit()
        return True

    # Method to take most of the finicky stuff out of adding an esp - just pass in the name of the scenario, the
    # xpath of the esp, and its score, and the method will take care of all the checks and things
    @staticmethod
    def public_add_esp(scen_name, xpath, score, data):
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            if ESP.esp_exists(xpath, score, data):
                curr = ESP.get_esp(xpath, score, data)
            else:
                curr = ESP(xpath, score, data)
            scen.add_esp(curr)
            return True
        else:
            return False


    # Method to take the work out of removing an esp from a scenario- pass in the scenario name and the xpath of the esp
    # to remove. The method runs a query to get the specific esp that is related to the given scenario and then removes
    # it without deleting the esp itself, since it may be related to other scenarios
    @staticmethod
    def public_remove_esp(scen_name, xpath, data, score):
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            esp_to_remove = scen.get_single_esp_for_scen(xpath, score, data)
            if esp_to_remove is not None:
                scen.remove_esp(esp_to_remove)
                scen.date_updated = Scenario.get_current_time()
                return True, ''
            else:
                return False, 'ESP %s no longer exists' % xpath
        else:
            return False, '%s no longer exists as a scenario' % scen_name

    # Method to allow editing an esp that a scenario already contains
    @staticmethod
    def edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score):
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            curr = scen.get_single_esp_for_scen(old_xpath, old_score, old_data)
            # ESPs with equivalents get their own editing part since they are created specifically for each scenario
            if curr is not None:
                if ESP.esp_exists(xpath, score, data):
                    scen.remove_esp(curr)
                    curr = ESP.get_esp(xpath, score, data)
                    scen.add_esp(curr)
                # otherwise we must create the new ESP and then add it to the scenario
                else:
                    scen.remove_esp(curr)
                    curr = ESP(xpath, score, data)
                    scen.add_esp(curr)
                scen.date_updated = Scenario.get_current_time()
                return True, ''
            else:
                return False, 'ESP %s no longer exists' % xpath
        else:
            return False, '%s no longer exists as a scenario' % scen_name

    def add_esp(self, esp):
        self.esps.append(esp)
        self.date_updated = Scenario.get_current_time()
        db.session.commit()
        return esp

    def remove_esp(self, esp):
        self.esps.remove(esp)
        self.date_updated = Scenario.get_current_time()
        db.session.commit()

    # Returns a list of all the scenarios in the database. Used by scenarios class.
    @staticmethod
    def get_scenarios():
        return Scenario.query.order_by(asc(Scenario.name)).all()

    # ToString method for scenarios
    def __repr__(self):
        return "Scenario: %r %r %r %r" % (self.name, self.description, self.doctype, self.fulfillmenttype)

    def serialize(self):
        return {'name': self.name,
                'description': self.description,
                'doctype': self.doctype,
                'fulfillmenttype': self.fulfillmenttype
                }

    # formatting can be found here: http://www.saltycrane.com/blog/2008/06/how-to-get-current-date-and-time-in/
    @staticmethod
    def get_current_time():
        date = datetime.datetime.now()
        # date = date.strftime("%m/%d/%y %H:%M")
        return date


# tables from another database for storing information on the usage of this web app
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

    def __repr__(self):
        return '<Appinfo: %r, %r, %r, %r, #r>' % (self.ip, self.starttime, self.processtime, self.error)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'ip': self.ip,
            'starttime': self.starttime,
            'processtime': self.processtime,
            'error': self.error,
            'misc': self.misc
        }


class Apps(db.Model):
    __bind_key__ = 'usagedb'
    __tablename__ = 'apps'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True)
    appinfo = db.relationship('Appinfo', backref='App',
                              order_by='Appinfo.id', lazy='dynamic',
                              cascade='all, delete, delete-orphan')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<appname %r>' % (self.name)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'app_id': self.id,
            'name': self.name,
            'app_info': [item.serialize for item in self.appinfo.all()]
        }


# ------------------- Apps -------------------- #
def add_app(a):
    if db.session.query(exists().where(Apps.name == a)).scalar():
        return get_app(a)
    else:
        entry = Apps(name=a)
        db.session.add(entry)
        db.session.commit()
        return entry


def get_app(n):
    return Apps.query.filter_by(name=n).first()


def get_apps():
    return Apps.query.all()


# ------------------- Appinfo -------------------- #
def add_info(app_id, ip_address, ptime, err, m):
    if db.session.query(exists().where(Apps.id == app_id)).scalar():
        # a = Apps.query.filter_by(id=app_id).first()
        t = Appinfo(ip=ip_address, processtime=ptime,
                    error=err, misc=m, fn_app=app_id)
        db.session.add(t)
        db.session.commit()
        return t


if __name__ == '__main__':
    manager.run()
