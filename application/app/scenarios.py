from app import db, models


class Scenario:
    # Get all of the scenarios in the database as a list
    @staticmethod
    def get_scenarios():
        reformat_list = []
        scen_list = models.Scenario.get_scenarios()
        for data in scen_list:
            reformat_list.append(
                {'name': data.name, 'schema': data.schema, 'description': data.description, 'doctype': data.doctype,
                 'fulfillmenttype': data.fulfillmenttype, 'date_created': data.date_created,
                 'date_updated': data.date_updated})
        return reformat_list

    @staticmethod
    def exists(name):
        return models.Scenario.check_exists(name)

    @staticmethod
    def create_scenario(name, schema, description, doctype, fulfillmenttype, esps):
        # print('%r %r %r %r %r %r' % (name, schema, description, doctype, fulfillmenttype, esps))
        name_available = not Scenario.exists(name)
        if name_available:
            scenario = models.Scenario.create_scenario(name, schema, description, doctype, fulfillmenttype)
            if scenario is not None:
                print(esps)
                for esp in esps:
                    xpath = esp['xpath']
                    score = esp['score']
                    data = esp['data']
                    if models.ESP.esp_exists(xpath, score, data):  # get esp if already exists
                        this_esp = models.ESP.get_esp(xpath, score, data)
                    else:  # create new esp
                        this_esp = models.ESP(xpath, score, data)
                    if scenario.get_single_esp_for_scen(this_esp.xpath, this_esp.score, this_esp.data) is None:
                        scenario.add_esp(this_esp)
            else:
                return False, "There was an issue creating scenario %s" % name
        else:
            return False, "%s already exists as a scenario" % name

        return True, ''

    @staticmethod
    def delete_scenario(name):
        return models.Scenario.delete_scenario(name)

    @staticmethod
    def copy_scenario(old_name, new_name, new_description):
        name_available = not Scenario.exists(new_name)
        if name_available:
            if Scenario.exists(old_name):
                current_scenario = models.Scenario.get_scenario(old_name)
                print(current_scenario)
                schema = current_scenario.schema
                esps = current_scenario.get_esps_as_list()
                doctype = current_scenario.doctype
                fulfillmenttype = current_scenario.fulfillmenttype
                print(esps)
                return Scenario.create_scenario(new_name, schema, new_description, doctype, fulfillmenttype, esps)
            else:
                return False, '%s no longer exists as a scenario' % old_name
        else:
            return False, '%s already exists as a scenario' % new_name

    @staticmethod
    def edit_scenario(old_name, new_name, schema, description, doctpye, fulfillmenttype):
        if old_name == new_name or (not Scenario.exists(new_name) and Scenario.exists(old_name)):
            scenario = models.Scenario.get_scenario(old_name)
            scenario.edit(new_name, schema, description, doctpye, fulfillmenttype)
            return True, ''
        elif not Scenario.exists(old_name):
            return False, '%s no longer exists as a scenario' % old_name
        else:
            return False, '%s already exists as a scenario' % new_name

    @staticmethod
    def add_esp(scen_name, xpath, score, data):
        return models.Scenario.public_add_esp(scen_name, xpath, score, data)

    @staticmethod
    def remove_esp(scen_name, xpath, score, data):
        return models.Scenario.public_remove_esp(scen_name, xpath, score, data)

    @staticmethod
    def edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score):
        return models.Scenario.edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score)
