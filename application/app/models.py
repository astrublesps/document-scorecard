from flask import Flask
import datetime
from sqlalchemy import asc, func
from sqlalchemy.sql import exists
from sqlalchemy.ext.associationproxy import association_proxy
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand


# this info is used to migrate and update the database tables
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

# ==============================SCENARIO_GROUPS====================================================
# this table will keep track of which groups are in each scenario
scenario_groups = db.Table('scenario_groups',
                           db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
                           db.Column('scenario_id', db.Integer, db.ForeignKey('scenario.id'))
                           )

# ==============================GROUP_FIELDS====================================================
# This will be the many-to-many relationship between groups and fields
group_fields = db.Table('group_fields',
                        db.Column('field_id', db.Integer, db.ForeignKey('field.id')),
                        db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
                        )


# ==============================FIELDS====================================================
class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), index=True)
    score = db.Column(db.Integer)
    data = db.Column(db.String(300))
    not_equal = db.Column(db.Boolean)

    def __init__(self, name, score, data, not_equal):
        self.name = name
        self.score = score
        self.data = data
        self.not_equal = not_equal

    # Check to see whether a field is already in the database
    @staticmethod
    def field_exists(name, score, data, not_equal):
        return Field.query.filter(Field.name == name, Field.score == score,
                                  Field.data == data, Field.not_equal == not_equal).first() is not None

    # Return a field given its name, score, data, and not_equal boolean
    @staticmethod
    def get_field(name, score, data, not_equal):
        return Field.query.filter(Field.name == name, Field.score == score, Field.data == data,
                                  Field.not_equal == not_equal).first()

    # remove a particular esp from the database
    def delete_field(self, name):
        field = Field.query.filter_by(self.name == name)
        db.session.delete(field)
        db.session.commit()

    # ToString method for a field
    def __repr__(self):
        return '<Field %r>' % (str(self.id) + " | " + self.name + " | " +
                               str(self.score) + " | " + str(self.data) + " | " + self.not_equal)

    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'score': self.score,
                'data': self.data
                }


# ==============================GROUPS=============================================================
# each scenario will have a set of groups like this, each group will have a set of fields
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), index=True)
    qualifier_field = db.Column(db.String(100))
    scenario_groups = db.relationship('Group', secondary=scenario_groups,
                                   primaryjoin=(scenario_groups.c.group_id == id),
                                   backref=db.backref('groups', lazy='dynamic'))
    child_fields = db.relationship('Field', secondary=group_fields,
                                   primaryjoin=(group_fields.c.group_id == id),
                                   backref=db.backref('fields', lazy='dynamic'))

    def __init__(self, name, qualifier_field):
        self.name = name
        self.qualifier_field = qualifier_field

    # Check to see whether a group is already in the database
    @staticmethod
    def group_exists(group_id):
        return Group.query.filter(Group.id == group_id).first() is not None

    # Return a group given its id
    @staticmethod
    def get_group(group_id):
        return Group.query.filter(Group.id == group_id).first()

    # Method to check whether a group exists before creating it, create it, and commit it
    @staticmethod
    def create_group(name):
        if not Group.group_exists(name):
            group = Group(name, '')
            db.session.add(group)
            db.session.commit()
            return group
        else:
            return None

    # remove a particular group from the database
    def edit_group(self, name):
        self.name = name

    # Return a specific Field for this group
    def get_single_field(self, name, score, data, not_equal):
        return Group.query.join(group_fields).filter(group_fields.c.group_id == self.id, Field.name == name,
                                                     Field.score == score, Field.data == data,
                                                     Field.not_equal == not_equal).first()

    # Return all Fields for this group
    def get_fields(self):
        return Group.query.join(group_fields).filter(group_fields.c.group_id == self.id).first()

    def add_field(self, field):
        self.group_fields.append(field)
        db.session.commit()
        return field

    def remove_field(self, field):
        self.esps.remove(field)
        db.session.commit()

    # ToString method for a field
    def __repr__(self):
        return '<Group %r | %r | %r | %r | %r>' % (
            str(self.id), self.name, self.qualifier_field, self.scenario_groups, self.child_fields)

    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'qualifier_field': self.qualifier_field,
                'child_groups': self.scenario_groups
                }


# ==============================SCENARIOS==========================================================
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
    root_node = db.Column(db.String(200))
    scenario_groups = db.relationship('Group', secondary=scenario_groups,
                                   primaryjoin=(scenario_groups.c.scenario_id == id),
                                   backref=db.backref('scenarios', lazy='dynamic'))

    def __init__(self, name, schema, description, doctype, fulfillmenttype, root_node):
        if not Scenario.scenario_exists(name):
            self.name = name
            self.schema = schema
            self.description = description
            self.doctype = doctype
            self.fulfillmenttype = fulfillmenttype
            self.root_node = root_node
            self.date_created = Scenario.get_current_time()
            self.date_updated = Scenario.get_current_time()

    # Check to see if a scenario exists, given its name
    @staticmethod
    def scenario_exists(check_name):
        return Scenario.query.filter_by(name=check_name).first() is not None

    # Get a particular scenario from the database, given its name
    @staticmethod
    def get_scenario(scen_name):
        if Scenario.scenario_exists(scen_name):
            return Scenario.query.filter_by(name=scen_name).first()

    # Return groups (which will return fields) related to a specific scenario so that they can be manipulated
    # Used in the Compare and ScenarioList classes
    def get_groups(self):
        return Group.query.join(scenario_groups).filter(scenario_groups.c.scenario_id == self.id).order_by(
            asc(Group.name)).all()

    # Return a particular esp related to a specific scenario
    def get_single_group_for_scen(self,group_id):
        return Group.query.join(scenario_groups).filter(scenario_groups.c.scenario_id == self.id,
                                                        Group.id == group_id).first()

    # Method to check whether a scenario exists before creating it, create it, and commit it
    @staticmethod
    def create_scenario(name, schema, new_description, doctype, fulfillmenttype, root_node):
        if not Scenario.scenario_exists(name):
            scen = Scenario(name, schema, new_description, doctype, fulfillmenttype, root_node)
            db.session.add(scen)
            db.session.commit()
            return scen
        else:
            return None

    # Method to check that a scenario exists, delete, and commit the change
    @staticmethod
    def delete_scenario(name):
        if Scenario.scenario_exists(name):
            del_scen = Scenario.get_scenario(name)
            esps_to_delete = Group.query.join(scenario_groups).filter(
                scenario_groups.c.scenario_id == del_scen.id).all()
            for esp in esps_to_delete:
                del_scen.remove_esp(esp)
            db.session.delete(del_scen)
            db.session.commit()
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
    # name of the esp, and its score, and the method will take care of all the checks and things
    @staticmethod
    def public_add_group(scen_name, group_name):
        if Scenario.scenario_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            if Group.group_exists(group_name):
                curr = Group.get_group(group_name)
            else:
                curr = Group(group_name, '')
            group = scen.add_group(curr)
            if group:
                return True, group
            else:
                return False, 'Unable to add group %s to scenario %s' % (group_name, scen_name)
        else:
            return False, '%s no longer exists as a scenario' % scen_name

    # Method to take the work out of removing an esp from a scenario- pass in the scenario name and the name of the esp
    # to remove. The method runs a query to get the specific esp that is related to the given scenario and then removes
    # it without deleting the esp itself, since it may be related to other scenarios
    @staticmethod
    def public_remove_group(scen_name, group_id):
        if Scenario.scenario_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            group_to_remove = scen.get_single_group_for_scen(group_id)
            if group_to_remove is not None:
                scen.remove_group(group_to_remove)
                scen.date_updated = Scenario.get_current_time()
                return True, ''
            else:
                return False, 'Group %s no longer exists' % group_to_remove.name
        else:
            return False, '%s no longer exists as a scenario' % scen_name

    def add_group(self, group):
        print(group)
        self.scenario_groups.append(group)
        self.date_updated = Scenario.get_current_time()
        db.session.commit()
        print(group)
        return group

    def remove_group(self, group):
        self.scenario_groups.remove(group)
        self.date_updated = Scenario.get_current_time()
        db.session.commit()

    # Returns a list of all the scenarios in the database. Used by scenarios class.
    @staticmethod
    def get_scenarios():
        return Scenario.query.order_by(asc(Scenario.name)).all()

    # ToString method for scenarios
    def __repr__(self):
        return "Scenario: %r | %r | %r | %r | %r | %r" % (
            self.name, self.schema, self.description, self.doctype, self.fulfillmenttype, self.root_name)

    def serialize(self):
        return {'name': self.name,
                'schema': self.schema,
                'description': self.description,
                'doctype': self.doctype,
                'fulfillmenttype': self.fulfillmenttype,
                'root_name': self.root_name
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
