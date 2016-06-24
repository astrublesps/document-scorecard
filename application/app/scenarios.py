from app import db, models


class Scenario:
    # Get all of the scenarios in the database as a list
    @staticmethod
    def get_scenarios():
        reformat_list = []
        scen_list = models.Scenario.get_scenarios()
        for scenario in scen_list:
            reformat_list.append(
                {'scenId': scenario.id, 'name': scenario.name, 'schema': scenario.schema, 'description': scenario.description,
                 'doctype': scenario.doctype, 'fulfillmenttype': scenario.fulfillmenttype,
                 'root_node': scenario.root_node,
                 'date_created': scenario.date_created, 'date_updated': scenario.date_updated})
        return reformat_list

    @staticmethod
    def get_scenario(scen_id):
        return models.Scenario.get_scenario(scen_id)

    @staticmethod
    def exists(name):
        return models.Scenario.scenario_exists(name)

    @staticmethod
    def create_scenario(name, schema, description, doctype, fulfillmenttype, root_node, esps):
        # print('%r %r %r %r %r %r' % (name, schema, description, doctype, fulfillmenttype, esps))
        name_available = not Scenario.exists(name)
        if name_available:
            scenario = models.Scenario.create_scenario(name, schema, description, doctype, fulfillmenttype, root_node)
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
    def delete_scenario(scen_id):
        return models.Scenario.delete_scenario(scen_id)

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
    def edit_scenario(old_name, new_name, schema, description, docttpye, fulfillmenttype):
        if old_name == new_name or (not Scenario.exists(new_name) and Scenario.exists(old_name)):
            scenario = models.Scenario.get_scenario(old_name)
            scenario.edit(new_name, schema, description, docttpye, fulfillmenttype)
            return True, ''
        elif not Scenario.exists(old_name):
            return False, '%s no longer exists as a scenario' % old_name
        else:
            return False, '%s already exists as a scenario' % new_name

    # ----------------------------------GROUP FUNCTIONS-----------------------------------------------

    @staticmethod
    def get_groups(scen_id):
        print('get_groups')
        scenario = Scenario.get_scenario(scen_id)
        return models.Scenario.get_groups(scenario)

    @staticmethod
    def group_exists(scen_name):
        scenario = Scenario.get_scenario(scen_name)
        return True, models.Scenario.group_exists(scenario)

    @staticmethod
    def add_group(scen_id, group_name):
        return True, models.Scenario.public_add_group(scen_id, group_name)

    @staticmethod
    def edit_group(group_id, group_name):
        group = models.Group.get_group(group_id)
        return True, group.edit_group(group_name)

    @staticmethod
    def remove_group(scen_name, group_id):
        return True, models.Scenario.public_remove_group(scen_name, group_id)

    # ----------------------------------FIELD FUNCTIONS-----------------------------------------------

    @staticmethod
    def get_fields(scen_id):
        field_list = []
        groups = Scenario.get_groups(scen_id)
        print(groups)
        for group in groups:
            print(group)
            # field_list.append(group.get_fields())
            field_list.append({'groupId': group.id, 'groupName': group.name})
        return field_list

    @staticmethod
    def add_field(group_id, name, score, data, not_equal):
        group = models.Group.get_group(group_id)
        return group.add_field(name, score, data, not_equal)

    @staticmethod
    def remove_field(scen_name, xpath, score, data):
        return models.Scenario.public_remove_(scen_name, xpath, score, data)

    @staticmethod
    def edit_field(scen_name, old_xpath, old_data, old_score, xpath, data, score):
        return models.Scenario.edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score)
