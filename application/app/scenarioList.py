from app import db, models
import re

#ScenarioList maintains methods for manipulating scenarios and getting information about them
class ScenarioList:

    #Get all of the scenarios in the database as a list
    @staticmethod
    def get_list():
        reformat_list = []
        scen_list = models.Scenario.get_list()
        for data in scen_list:
           # reformat_list.append([ data.name,data.description]) 
             reformat_list.append({ 'name' : data.name, 'description' : data.description, 'doctype' : data.doctype, 'date_created': data.date_created, 'date_updated' : data.date_updated})
        return reformat_list

    #Deep copy a scenario that already exists as a new scenario with a new name and description
    @staticmethod
    def copy_scenario(name_of_old_scen, name_of_new_scen, descr_of_new_scen):
        old_scen_exists = models.Scenario.check_exists(name_of_old_scen)
        new_scen_exists = models.Scenario.check_exists(name_of_new_scen)
        esps = []
        esp_list = []
        equal_esps = []
        qual_reps = {}
        if new_scen_exists:
            return "Scenario %s already exists. Please choose a different name." % name_of_new_scen
        else:
            if old_scen_exists:
                #get together all the info on the scenario we're copying
                old_scen = models.Scenario.get_scenario(name_of_old_scen) 
                esps = old_scen.get_esps()
                doctype = old_scen.doctype
                copy_scen =  models.Scenario.create_scenario(name_of_new_scen, descr_of_new_scen, doctype)
                #translate the esps back into lists of dicts to pass into the build_scenario method
                for esp in esps:
                    if esp.is_qualifier():
                        qual_esp = models.ESP(esp.xpath, esp.score, esp.data, True)
                        copy_scen.add_esp(qual_esp)
                        for child in esp.get_qual_children():
                            qual_esp.add_child(child) 
                    elif esp.has_equals():
                        copy_scen.add_esp(esp)
                        for equal in esp.get_equals():
                            esp.add_equal_element(equal)
                    else:
                        copy_scen.add_esp(esp)
                return True
            else:
                return "Scenario %s no longer exists." % name_of_old_scen

    #Rename a scenario that already exists
    @staticmethod
    def rename_scenario(old_name, new_name):
        scen_exists = models.Scenario.check_exists(old_name)
        new_scen_exists = models.Scenario.check_exists(new_name)
        if new_scen_exists:
            return "Scenario %s already exists. Please choose a different name." % new_name
        else:
            if scen_exists:
                scen_to_rename = models.Scenario.get_scenario(old_name)
                scen_to_rename.rename(new_name)
                return True
            else:
                return "Scenario %s no longer exists." % old_name

    #Permanently remove a scenario from the database
    @staticmethod
    def delete_scenario(delete_scen_name):
        success = models.Scenario.delete_scenario(delete_scen_name)
        return success

    #Create a new scenario in the database with a name (unique string), description (string), and list of esps
    @staticmethod
    def build_scenario(name, description, doctype, esps, equal_esps, qualified_reps):
        name_in_use = models.Scenario.check_exists(name)
        edited_xpath_scores = []
        if name_in_use is False:
            scenario = models.Scenario.create_scenario(name, description, doctype)
            if scenario is not None:
                #data['xpath'] is xpath, data['score'] is score, data['data'] is a string the field should contain, e.g. ST or TPID525
                for data in esps:
                    score_is_int = False
                    xpath = data['xpath']
                    #check to make sure the score contains an integer
                    try:
                        parse_score = int(data['score'])
                        score_is_int = True
                    except ValueError:
                        edited_xpath_scores.append(xpath+data['data'])
                    if score_is_int:
                        if parse_score > 0 and parse_score < 6 and models.ESP.esp_exists(xpath, parse_score, data['data'], False):
                            e = models.ESP.get_esp(xpath, parse_score, data['data'], False)
                        else:
                            #check to make sure the score is between 1 and 5
                            if parse_score > 5:
                                e = models.ESP(xpath, 5, data['data'])
                                edited_xpath_scores.append(xpath+data['data'])
                            elif parse_score < 1:
                                e = models.ESP(xpath, 1, data['data'])
                                edited_xpath_scores.append(xpath+data['data'])
                            else:
                                e = models.ESP(xpath, parse_score, data['data'])
                    else:
                        e = models.ESP(xpath, 5, data['data'])    
                    if scenario.get_single_esp_for_scen(e.xpath, e.score, e.data) is None:
                        scenario.add_esp(e)

                # if there are esps that can be equated in a scenario, they should belong to that specific scenario,
                # otherwise it could get confusing. this part creates and selects esps for the scenario that is currently being built
                # and manipulates them only.
                for equal in equal_esps:
                   e_xpath = equal[0]['xpath']
                   try:
                        e_score = int(equal[0]['score'])
                   except ValueError:
                        edited_xpath_scores.append(e_xpath+equal[0]['data'])
                        e_score = 5
                   if e_score > 5 or e_score < 1:
                        e_score = 5
                   e = scenario.get_single_esp_no_score(e_xpath, equal[0]['data'])
                   if e is None:
                       e = models.ESP(e_xpath, e_score, equal[0]['data'])
                       scenario.add_esp(e)
                   f_xpath = equal[1]['xpath']
                   f = scenario.get_single_esp_no_score(f_xpath, equal[0]['data'])
                   if f is None:
                       f = models.ESP(f_xpath, e_score, equal[0]['data'])
                       scenario.add_esp(f)
                   if not e.equal_relationship_exists(f):
                       e.add_equal_element(f)

                #Create qualified repetitions of a group, e.g. Address where AddressTypeCode=ST
                #First the qualifier is added to the scenario as an ESP, and then relationships between
                # the qualifying field and the other required fields in that rep are created in the qual_children table.
                # If there are other qualifiers in the rep, they are added as children of the first qualifier just like
                # the regular ESPs, but they are set as qualifiers in the database and will be checked when doing comparisons.
                # Having only one main qualifier with all other qualifiers and required fields as children simplifies
                # comparisons and the creation of output.
                for key in qualified_reps:
                    group = qualified_reps[key]
                    qual_field = scenario.get_single_esp_for_scen(group[0]['xpath'],group[0]['score'],group[0]['data'])
                    if qual_field is None:
                        qual_field = models.ESP(group[0]['xpath'],group[0]['score'],group[0]['data'], group[0]['is_qual'])
                        scenario.add_esp(qual_field)
                    for qual_child in group:
                        child = models.ESP.get_esp(qual_child['xpath'],qual_child['score'],qual_child['data'],qual_child['is_qual'])
                        if child is None:
                            child = models.ESP(qual_child['xpath'],qual_child['score'],qual_child['data'], qual_child['is_qual'])
                        qual_field.add_child(child)
                    scen_test = models.Scenario.get_scenario(name)
                scen_test = models.Scenario.get_scenario(name)
                if len(edited_xpath_scores) > 0:
                    return edited_xpath_scores
                else:
                   return True
        else:
           return False
