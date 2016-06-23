import os
import time
from flask import render_template, flash, redirect, url_for, request, make_response, Response, json
from app import app, scenarios, models, compare, output, parser, schemaValidation, schemaOrder
from werkzeug import secure_filename
import re

# This script is the interface between the user interface in the form of webpages, and the classes that perform
# the manipulations of data
ALLOWED_EXTENSIONS = ['txt', 'xml']


# main page
@app.route('/')
@app.route('/index')
def documentscorecard_index():
    return render_template("index.html", scenarios=get_scenarios())


def log_error(error):
    app.logger.info(error)


# function to get the list of all scenarios
@app.route('/get_scenarios')
def get_scenarios():
    return Response(json.dumps(scenarios.Scenario.get_scenarios()), mimetype='application/json')


# function to check whether the uploaded file is a type of file that can be accepted by the application
def file_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# accepts an uploaded file and parses it into a new scenario with a name, description, and esps
@app.route('/upload_new_scenario', methods=['POST'])
def upload_new_scenario():
    if request.method == 'POST':
        file = request.files['file']
        data = json.loads(request.form['data'])
        name = data['name']
        if 'schema' in data:
            schema = data['schema']
        else:
            schema = ''
        description = data['description']
        doctype = data['docType']
        if 'fulfillmentType' in data:
            fulfillmenttype = data['fulfillmentType']
        else:
            fulfillmenttype = ''
        is_valid = False
        if file:
            if file_allowed(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                input_data, parse_error = parser.Parser.scenario_parse(app.config['UPLOAD_FOLDER'] + '/' + filename)
                if len(parse_error) > 0:
                    return make_response(parse_error, 400)
                if isinstance(input_data, list):
                    is_valid = True
            else:
                return make_response("File type must be .xml or .txt.", 400)
        else:
            return make_response("Please upload a file to create this scenario.", 400)
        if is_valid:
            esps = input_data
            result, creating_scenario_error = scenarios.Scenario.create_scenario(name, schema, description, doctype,
                                                                                 fulfillmenttype, '', esps)
            if result is False:
                return make_response(creating_scenario_error, 400)
        return get_scenarios()


# accepts just a name and description for a new blank scenario
@app.route('/create_scenario', methods=['POST'])
def create_scenario():
    if request.method == 'POST':
        name = request.json['name']
        if 'schema' in request.json:
            schema = request.json['schema']
        else:
            schema = ''
        description = request.json['description']
        doctype = request.json['docType']
        if 'fulfillmentType' in request.json:
            fulfillmenttype = request.json['fulfillmentType']
        else:
            fulfillmenttype = ''
        if 'rootName' in request.json:
            root_name = request.json['rootName']
        else:
            root_name = ''
        result, create_error = scenarios.Scenario.create_scenario(name, schema, description, doctype, fulfillmenttype,
                                                                  root_name, [])
        if result is False:
            return make_response(create_error, 400)
        return get_scenarios()


# deletes a scenario if it exists
@app.route('/delete_scenario', methods=['POST'])
def delete_scenario():
    if request.method == 'POST':
        name = request.json['name']
        if not scenarios.Scenario.exists(name):
            return make_response("Scenario %s does not exist" % name, 400)
        if not scenarios.Scenario.delete_scenario(name):
            return make_response("Unable to delete scenario %s" % name, 400)
        return get_scenarios()


# makes a copy of a scenario that already exists
@app.route('/copy_scenario', methods=['POST'])
def copy_scenario():
    if request.method == 'POST':
        name_of_old_scen = request.json['oldName']
        name_of_new_scen = request.json['name']
        description_of_new_scen = request.json['description']
        if len(name_of_old_scen) > 0 and len(name_of_new_scen) > 0:
            result, copy_error = scenarios.Scenario.copy_scenario(name_of_old_scen, name_of_new_scen,
                                                                  description_of_new_scen)
            if result is False:
                return make_response(copy_error, 400)
        return get_scenarios()


# edit a scenario that already exists
@app.route('/edit_scenario', methods=['POST'])
def edit_scenario():
    if request.method == 'POST':
        new_name = request.json['name']
        old_name = request.json['oldName']
        if 'schema' in request.json:
            schema = request.json['schema']
        else:
            schema = ''
        description = request.json['description']
        doctype = request.json['docType']
        if 'fulfillmentType' in request.json:
            fulfillmenttype = request.json['fulfillmentType']
        else:
            fulfillmenttype = ''
        result, edit_error = scenarios.Scenario.edit_scenario(old_name, new_name, schema, description, doctype,
                                                              fulfillmenttype)
        if result is False:
            return make_response(edit_error, 400)
        return get_scenarios()


# ----------------------------------GROUP FUNCTIONS-----------------------------------------------

# adds a single group to a specified scenario
@app.route('/add_group', methods=['POST'])
def add_group():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        group_name = request.json['groupName']
        result, group_error = scenarios.Scenario.add_group(scen_name, group_name)
        if result is False:
            return make_response(group_error, 500)
        return field_list(scen_name)


# edit a single group to a specified scenario
@app.route('/edit_group', methods=['POST'])
def edit_group():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        group_id = request.json['groupID']
        group_name = request.json['groupName']
        result, group_error = scenarios.Scenario.edit_group(group_id)
        if result is False:
            return make_response(group_error, 500)
        return field_list(scen_name)


# remove a single group to a specified scenario
@app.route('/remove_group', methods=['POST'])
def remove_group():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        group_id = request.json['groupID']
        result, group_error = scenarios.Scenario.remove_group(scen_name, group_id)
        if result is False:
            return make_response(group_error, 500)
        return field_list(scen_name)


# ----------------------------------FIELD FUNCTIONS-----------------------------------------------

# returns a list of esps to the webpage when the scenario is initially clicked to load the fields
@app.route('/get_fields', methods=['POST'])
def get_fields():
    if request.method == 'POST':
        name = request.json['name']
        return field_list(name)


@app.route('/get_fields2', methods=['POST'])
def get_fields2():
    if request.method == 'POST':
        scen_name = request.json['name']
        return output.Output.get_scenario_as_xml_tree(scen_name)


# returns a list of fields grouped by the groups they are in
def field_list(name):
    exists = models.Scenario.scenario_exists(name)
    if exists:
        scenario_fields = scenarios.Scenario.get_fields(name)
        return Response(json.dumps(scenario_fields), mimetype='application/json')
    else:
        return make_response('That scenario does not exist', 400)


# Simply check that score is valid
def check_score(score):
    if score:
        try:
            score = int(score)
        except ValueError:
            return False, 'Score must be an integer, not %s' % score
        if int(score) < 1 or int(score) > 5:
            return False, 'Score must be an integer between 1 and 5, not %s' % score
        return True, ''
    else:
        return False, 'Score is required'


# adds a single given esp to a specified scenario
@app.route('/add_field', methods=['POST'])
def add_field():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        xpath = request.json['xpath']
        score = request.json['score']  # is an int
        data = ''
        if 'data' in request.json:
            data = request.json['data']
        result, check_score_error = check_score(score)
        if result is False:
            return make_response(check_score_error, 500)
        if not scenarios.Scenario.add_esp(scen_name, xpath, score, data):
            return make_response('Scenario %s no longer exists' % scen_name, 500)
        return field_list(scen_name)


# removes one esp from a particular scenario
@app.route('/remove_field', methods=['POST'])
def remove_field():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        xpath = request.json['xpath']
        data = request.json['data']
        score = request.json['score']
        result, remove_error = scenarios.Scenario.remove_esp(scen_name, xpath, data, score)
        if result is False:
            return make_response(remove_error, 500)
        return field_list(scen_name)


# removes one esp from a particular scenario
@app.route('/edit_field', methods=['POST'])
def edit_field():
    if request.method == 'POST':
        scen_name = request.json['scenName']
        old_xpath = request.json['oldXpath']
        old_data = request.json['oldData']
        old_score = request.json['oldScore']
        try:
            xpath = request.json['newXpath']
        except KeyError:
            xpath = old_xpath
        try:
            data = request.json['newData']
        except KeyError:
            data = ''
        try:
            score = request.json['newScore']
        except KeyError:
            score = old_score
        print(xpath)
        print(data)
        print(score)
        result, edit_error = scenarios.Scenario.edit_esp(scen_name, old_xpath, old_data, old_score, xpath, data, score)
        if result is False:
            return make_response(edit_error, 500)
        return field_list(scen_name)


# The most important function of the application. Uploads an input file, checks to see if it's the right kind of file,
# then sends it to the output class, which parses it and compares it one or more given scenarios and sends back a string
# from which this function creates a downloadable txt file with the results of the comparison
@app.route('/compare_download', methods=['POST'])
def compare_download():
    start_time = time.time()
    if request.method == 'POST':
        file = request.files['file']
        print('file: OK')
        data = json.loads(request.form['data'])
        selected_list = data['testList']
        print('testList: OK')
        also_check_content = True
        error = ''
        down_file = ''
        valid_input = False
        input_data = []
        if len(selected_list) > 0:
            if file and file_allowed(file.filename):  # check whether this is an ok file type
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                input_data, empty_nodes, tree = parser.Parser.input_parse(app.config['UPLOAD_FOLDER'] + '/' + filename)
                if isinstance(input_data,
                              dict) and not input_data == "Error":  # check to see that parsing the file was successful
                    valid_input = True
                else:
                    error += "Error parsing %s. Please check that file is valid XML." % file.filename

            else:
                error = "File type or name is not allowed."

            if valid_input:
                down_file = output.Output.create_file(input_data, empty_nodes, tree, selected_list, also_check_content)

                if down_file.startswith(
                        "Error"):  # there was an error in file creation; type of error specified in the error string
                    error += down_file
                else:
                    # make a downloadable file
                    scens = selected_list.split(",")
                    record_usage(float("{0:.3f}".format(time.time() - start_time)), False,
                                 (str(len(scens)) + " scenarios" + "- " + selected_list))
                    response = make_response(down_file)
                    response.headers["Content-Disposition"] = "attachment; filename=%s-DSC.txt" % filename.rsplit('.')[
                        0]
                    return response
        else:
            error = "Please select a Scenario to compare your input against."
        if len(error) < 1:
            return redirect('/documentscorecard' + url_for('index'))
        else:
            print(error)
            record_usage(float("{0:.3f}".format(time.time() - start_time)), True, selected_list)
            response = make_response(error, 400)
            return response


@app.route('/download_esp_list', methods=['POST'])
def download_esp_list():
    if request.method == 'POST':
        selected_list = ''
        scen_name = request.json['name']
        schema_name = request.json['schema']
        print(scen_name)
        down_file = output.Output.get_scenario_as_xml_tree(scen_name)
        with open('dsc.xml', 'wb') as w:
            w.write(down_file)
        print('dsc.xml')
        down_file = schemaOrder.order.order_xml('dsc.xml', schema_name)
        print(down_file)

        with open(app.config['APP_FOLDER'] + '/output.xml', 'r') as r:
            strr = r.read()
        response = make_response(strr)
        response.headers["Content-Disposition"] = "attachment;filename=%s-requirements.txt" % selected_list.replace(
            ",", "-")
        return response


def record_usage(processing_time, err, misc):
    app_id = int(models.get_app(app.config['APP_NAME']).id)
    models.add_info(app_id, request.environ.get('HTTP_X_REAL_IP', request.remote_addr), processing_time, err, misc)


# --------------------SCHEMA VALIDATION------------------------------------------
# function to check whether the uploaded schema has a valid '.xsd' file extension
@app.route('/get_schema_list', methods=['GET'])
def get_schema_list():
    return json.dumps(schemaValidation.validate.get_schema_list())


@app.route('/add_schema', methods=['POST'])
def add_schema():
    if request.method == 'POST':
        file = request.files['file']
        data = json.loads(request.form['data'])
        schema_name = data['schema']
        if file:
            result, error = schemaValidation.validate.add_schema(file, schema_name)
            if result is False:
                return make_response(error, 400)
        else:
            return make_response("A schema must be upload.", 400)
    return get_schema_list()


@app.route('/delete_schema', methods=['POST'])
def delete_schema():
    filename = request.json['delete']
    # if this is empty, schema was successfully deleted
    result, error = schemaValidation.validate.delete_schema(filename)
    if result is False:
        return make_response(error, 400)
    return get_schema_list()
