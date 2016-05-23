from flask import Flask
import datetime
from sqlalchemy import asc,func
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

#This code is the interface between python and the actual database. The methods are queries created in python that are
#translated into SQL using sqlalchemy

#contains is relationship table for the many-to-many relationship between ESPs and Scenarios
#it has foreign keys for the esps and for the scenarios
contains = db.Table('contains',
                    db.Column('esp_id', db.Integer, db.ForeignKey('ESP.id')),
                    db.Column('scenario_id', db.Integer, db.ForeignKey('scenario.id'))
                    )

#Many-to-many table from ESP to ESP, to keep track of equivalency relationships.
#If a scenario just wants to make sure that one of BPN, UPC, or GTIN is present,
#this table keeps track of which ESPs are equivalent to which other ESPs.
#Equivalent ESPs are specific to one particular scenario, and are created and deleted along with that scenario.
esp_groups = db.Table('esp_groups',
                     db.Column('esp_me_id', db.Integer, db.ForeignKey('ESP.id')),
                     db.Column('esp_equal_to_id', db.Integer, db.ForeignKey('ESP.id'))
                     )

#qual_children is the table for storing all the relationships of  esps that must be included in a qualified repetition. The ESP(s) that is/are the qualifier
#is added to the scenario as an esp, but all the fields within that group are only related to the qualifier ESPs through this many-to-many
#table, and are not added to the scenario itself. This way, checking for those esps is done exclusively through the qualifiers,
#so if there are multiple of the same group, eg Address where AddressTypeCode=VN and Address where AddressTypeCode=ST, and only
#the ST rep has certain required fields, only the ST rep will be check for those fields and the VN rep will be left alone.
#qualifying fields are set up using '[qualified rep]' in the text for the field in an uploaded .txt or .xml file containing the scenario.
qual_children = db.Table('qual_children',
                     db.Column('qual_esp_id', db.Integer, db.ForeignKey('ESP.id')),
                     db.Column('qual_child_esp_id', db.Integer, db.ForeignKey('ESP.id'))
                     )

#ESP is the table for the esps. It has id (used for the database), score, xpath, and data columns
#For esps, the combination of xpath, score, and data is unique in the table. This is for efficiency, since there are
# only 5 possible scores, there is likely to be a lot of overlap in the esps that scenarios contain.
class ESP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    data = db.Column(db.String(300))
    xpath = db.Column(db.String(500), index=True)
    requires_one = db.Column(db.String(500))
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

    def __init__(self, xpath, score, data, requires_one, qual=False):
        self.score = score
        self.xpath = xpath
        self.data = data
        self.requires_one = requires_one
        self.is_qual = qual

    #Check to see whether an esp is already in the database
    @staticmethod
    def esp_exists(check_xpath, check_score, check_data,qual_stat):
        return ESP.query.filter(ESP.xpath==check_xpath, ESP.score==check_score, ESP.data==check_data, ESP.equal_elements==None, ESP.is_qual==qual_stat).first() is not None

    #Return an esp given its score and xpath, but only esps with no equals.
    @staticmethod
    def get_esp(get_xpath, get_score, get_data, qual_stat):
        return ESP.query.filter(ESP.xpath==get_xpath, ESP.score==get_score, ESP.data==get_data, ESP.equal_elements==None, ESP.is_qual==qual_stat).first()

    #remove a particular esp from the database
    def delete_esp(self, name):
        esp = ESP.query.filter_by(self.name == name)
        db.session.delete(esp)
        db.session.commit()

    #add an equivalency relationship to this esp with the passed-in esp
    def add_equal_element(self, equal_element):
        if not self.equal_relationship_exists(equal_element):
            self.equal_elements.append(equal_element)
            db.session.commit()

    #check to see whether the calling esp has the passed-in esp as an equivalent.
    #this method is set up so for two equivalent esps, each one will have a separate relationship link
    #for example, if BPN and VPN are equivalent, BPN will have an equal_element relationship with VPN delineated in esp_groups,
    #and VPN will have another equal_element relationship with BPN delineated in esp_groups.
    #This is to make checking for equivalent esps simpler.
    def equal_relationship_exists(self, equal_element):
        #print("checking %s %s" % (self.xpath, equal_element.xpath))
        if self.id == equal_element.id:
            return True
        if self.equal_elements.filter(esp_groups.c.esp_equal_to_id==equal_element.id).count() > 0:
            return True
        return False

    #checks to see whether the calling esp has any equivalents, not a specific one
    def has_equals(self):
        #print("\n" + str(self.equal_elements.count()))
        return self.equal_elements.count() > 0

    #returns all the equivalents for a specific esp
    def get_equals(self):
        return self.equal_elements.all()

    #add the passed-in esp as a required field but only within the context of a qualified repetition
    def add_child(self, esp):
        self.is_qual = True
        if self.children.filter(qual_children.c.qual_child_esp_id==esp.id).count() < 1:
            self.children.append(esp)
            db.session.commit()

    #remove the passed-in esp as a required field from a qualified repetition
    def remove_child(self, esp):
        self.children.remove(esp)
        db.session.commit()
        if self.children.count() < 1:
            self.is_qual = False

    #helper method for deleting a qualified repetition
    def remove_all_children(self):
        self.children = []
        db.session.commit()

    #check whether the ESP is a qualifier field for a qualified repetition
    def is_qualifier(self):
        return self.is_qual

    #return a list of all the required fields for a qualified repetition
    def get_qual_children(self):
        return self.children.all()

    #if there are multiple qualifiers for a qualified repetition, this returns the other qualifiers
    def get_other_qualifiers(self):
        if self.is_qual:
            return self.children.filter(ESP.is_qual==True).all()
        else:
            return None

    #ToString method for an esp
    def __repr__(self):
        return '<ESP %r>' % (str(self.id) + " " + self.xpath + " " + str(self.score) + " " + str(self.data) + " " + str(self.is_qual))

    def serialize(self):
        return {'id': self.id,
                'xpath': self.xpath,
                'score': self.score,
                'data': self.data
                }

#Scenario is the table for scenarios. Each scenario has a unique name, non-unique description, and a relationship with
#zero or more esps through the contains table.
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

    def __init__(self, name, schema, description, fulfillmenttype, doctype='000'):
        if not Scenario.check_exists(name):
            self.name = name
            self.schema = schema
            self.description = description
            self.doctype = doctype
            self.fulfillmenttype = fulfillmenttype
            self.date_created = datetime.datetime.now()
            self.date_updated = datetime.datetime.now()

    #Check to see if a scenario exists, given its name
    @staticmethod
    def check_exists(check_name):
        return Scenario.query.filter_by(name=check_name).first() is not None

    #Get a particular scenario from the database, given its name
    @staticmethod
    def get_scenario(scen_name):
        if Scenario.check_exists(scen_name):
            return Scenario.query.filter_by(name=scen_name).first()

    #Return esps related to a specific scenario as esps, or objects, so that they can be manipulated
    #Used in the Compare and ScenarioList classes
    def get_esps(self):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id).order_by(asc(ESP.xpath)).all()

    #Return a particular esp related to a specific scenario
    def get_single_esp_for_scen(self, g_xpath, g_score, g_data):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id, ESP.xpath==g_xpath, ESP.score==g_score, ESP.data==g_data).first()

    #Return a specific ESP for this scenario, but without checking score (since there should only be one score for any given
    # xpath/data combo, e.g. AddressTypeCode where data is ST can only have one score per scenario. Used in ScenarioList.build_scenario()
    def get_single_esp_no_score(self, g_xpath, g_data):
        return ESP.query.join(contains).filter(contains.c.scenario_id == self.id, ESP.xpath==g_xpath, ESP.data==g_data).first()

    #Return esps related to a specific scenario as a list, so that they can be read
    #Used in the ScenarioList class
    def get_esps_as_list(self):
        all_esps = ESP.query.join(contains).filter(contains.c.scenario_id == self.id).order_by(asc(ESP.xpath)).all()
        list_of_esps = []
        for data in all_esps:
            x = {'xpath' : data.xpath, 'data' : data.data, 'score' : data.score}
            list_of_esps.append(x)
            if data.is_qual:
                quals = data.get_other_qualifiers()
                qual_str = ' where '
                for q in quals:
                    qual_str += "%s is %s " % (q.xpath.split('/')[-1],q.data)
                for child in data.get_qual_children():
                    x = {'xpath' : (child.xpath + qual_str), 'data' : child.data, 'score' : child.score}
                    list_of_esps.append(x)
        return list_of_esps

    #Method to check whether a scenario exists before creating it, create it, and commit it
    @staticmethod
    def create_scenario(new_name, new_description, doctype):
        if not Scenario.check_exists(new_name):
            scen = Scenario(new_name, new_description, doctype)
            db.session.add(scen)
            db.session.commit()
            return scen
        else:
            return False

    #Method to check that a scenario exists, delete, and commit the change
    @staticmethod
    def delete_scenario(del_name):
        if Scenario.check_exists(del_name):
            del_scen = Scenario.get_scenario(del_name)
            esps_to_delete = ESP.query.join(contains).filter(contains.c.scenario_id == del_scen.id).filter(ESP.equal_elements!=None).all()
            #delete any esps with equivalency relationships, since those are created to be scenario specific and will not be re-used
            for esp in esps_to_delete:
                 #print("delete esp" + str(esp))
                 db.session.delete(esp)
            esps_to_delete = ESP.query.join(contains).filter(contains.c.scenario_id == del_scen.id).filter(ESP.is_qual==True).all()
            for esp in esps_to_delete:
                esp.remove_all_children
                db.session.delete(esp)
            db.session.delete(del_scen)
            db.session.commit()
            #cleanup db
            esps_to_delete = ESP.query.outerjoin(contains).filter(contains.c.scenario_id == None).all()
            for esp in esps_to_delete:
                if ESP.query.join(qual_children, (ESP.id == qual_children.c.qual_child_esp_id)).filter(esp.id == qual_children.c.qual_child_esp_id).first() is None:
                    print(esp.xpath)
                    db.session.delete(esp)
            db.session.commit()
            return True
        else:
            return False

    def rename(self, new_name):
        self.name = new_name
        self.date_updated = datetime.datetime.now()
        db.session.commit()
        return True


    #Method to take most of the finicky stuff out of adding an esp - just pass in the name of the scenario, the
    #xpath of the esp, and its score, and the method will take care of all the checks and things
    @staticmethod
    def public_add_esp(scen_name, xpath, score, data):
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            if ESP.esp_exists(xpath, score, data, False):
                curr = ESP.get_esp(xpath, score, data)
            else:
                curr = ESP(xpath, score, data)
            scen.add_esp(curr)
            return True
        else:
            return False

    #Method to allow editing an esp that a scenario already contains
    @staticmethod
    def edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score, quals):
#        print("models %s %s %s %s %s %s %s" % (scen_name, old_xpath, old_data, str(old_score), xpath, data, str(score)))
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            curr = scen.get_single_esp_for_scen(old_xpath, old_score, old_data)
            #ESPs with equivalents get their own editing part since they are created specifically for each scenario
            if curr is not None:
                if curr.has_equals():
                    equivalents = curr.get_equals();
                    new_esp = ESP(xpath, score, data)
                    scen.add_esp(new_esp)
                    for e in equivalents:
                        equ = ESP(e.xpath, score, data)
                        scen.add_esp(equ)
                        new_esp.add_equal_element(equ)
                        equ.add_equal_element(new_esp)
                        Scenario.public_remove_esp(scen.name, e.xpath, e.data, e.score)
                    Scenario.public_remove_esp(scen.name, curr.xpath, curr.data, curr.score)
                #ESPs that are qualifiers get their own editing part since they are created specifically for each scenario
                elif curr.is_qualifier():
                    curr.xpath = xpath
                    curr.data = data
                    curr.score = score
                    db.session.commit()
                #if the ESP we're changing this ESP to already exists as an ESP, just not as a part of this scenario,
                # then we can just remove the old ESP and add the new one
                elif ESP.esp_exists(xpath, score, data, False):
                    scen.remove_esp(curr)
                    curr = ESP.get_esp(xpath, score, data, False)
                    scen.add_esp(curr)
                #otherwise we must create the new ESP and then add it to the scenario
                else:
                    scen.remove_esp(curr)
                    curr = ESP(xpath, score, data)
                    scen.add_esp(curr)
                scen.date_updated = datetime.datetime.now()
                return True
            elif quals:#if the ESP is not found and the qualifier list is non-empty, the ESP is a child of a qualified rep
                qualifiers = ESP.query.join(contains).filter(contains.c.scenario_id==scen.id, ESP.data == quals[1], ESP.is_qual==True).all()
                for qual in qualifiers:
                    if quals[0] in qual.xpath:
                        children = qual.get_qual_children()
                        for child in children:
                            if old_xpath == child.xpath and old_data == child.data and old_score == child.score:
                                qual.remove_child(child)
                                new_child = ESP(xpath, score, data)
                                qual.add_child(new_child)
                                return True

            else:
                return False
        else:
            return False


    def add_esp(self, esp):
        self.esps.append(esp)
        self.date_updated = datetime.datetime.now()
        db.session.commit()
        return esp

    #Method to take the work out of removing an esp from a scenario- pass in the scenario name and the xpath of the esp
    # to remove. The method runs a query to get the specific esp that is related to the given scenario and then removes
    # it without deleting the esp itself, since it may be related to other scenarios
    @staticmethod
    def public_remove_esp(scen_name, xpath, data, score, quals):
        if Scenario.check_exists(scen_name):
            scen = Scenario.get_scenario(scen_name)
            esp_to_remove = scen.get_single_esp_for_scen(xpath, score, data)
            if esp_to_remove is not None:
                if esp_to_remove.has_equals():
                    scen.remove_esp(esp_to_remove)
                    db.session.delete(esp_to_remove)
                    db.session.commit()
                elif esp_to_remove.is_qualifier():
                    esp_to_remove.remove_all_children()
                    scen.remove_esp(esp_to_remove)
                    db.session.delete(esp_to_remove)
                    db.session.commit()
                else:
                    scen.remove_esp(esp_to_remove)
                scen.date_updated = datetime.datetime.now()
                return True
            elif quals:#if the scenario doesn't have the ESP, it might be a child in a qualified rep.
                #get ESPs that are qualifiers for this scenario
                qualifiers = ESP.query.join(contains).filter(contains.c.scenario_id==scen.id, ESP.data == quals[1], ESP.is_qual==True).all()
                for qual in qualifiers:
                    if quals[0] in qual.xpath:
                        children = qual.get_qual_children()
                        for child in children:
                            if xpath == child.xpath and data == child.data and score == child.score:
                                qual.remove_child(child)
                                db.session.commit()
                                return True
                return False
            else:
                return False
        else:
            return False

    def remove_esp(self, esp):
        self.esps.remove(esp)
        self.date_updated = datetime.datetime.now()
        db.session.commit()

    #Returns a list of all the scenarios in the database. Used by ScenarioList class.
    @staticmethod
    def get_list():
        return Scenario.query.order_by(asc(Scenario.name)).all()

    #ToString method for scenarios
    def __repr__(self):
        return "Scenario: % r %r" %(self.name, self.description)

    def serialize(self):
        return { 'name': self.name,
                'description': self.description
                }

#tables from another database for storing information on the usage of this web app
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