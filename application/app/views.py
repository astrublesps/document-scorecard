import os
import time
from flask import render_template, flash, redirect, url_for, request, make_response, Response, json
from app import app, scenarioList, models, compare, output, parser, schemaValidation, schemaOrder
from werkzeug import secure_filename
import re

# This script is the interface between the user interface in the form of webpages, and the classes that perform
# the manipulations of data
ALLOWED_EXTENSIONS = ['txt', 'xml']


# main page
@app.route('/')
@app.route('/index')
def documentscorecard_index():
    return render_template("index.html", scenarios=get_scenario_list())


@app.route('/test_error', defaults={'error': 'There was an error.'})
@app.route('/test_<error>')
def index_error(error):
    log_error(error)
    return render_template("index.html", scenarios=get_scenario_list(), error=error)


def log_error(error):
    app.logger.info(error)


# function to get the list of all scenarios
@app.route('/get_scenario_list', methods=['GET'])
def get_scenario_list():
    if request.method == 'GET':
        return Response(json.dumps(scenarioList.ScenarioList.get_list()), mimetype='application/json')


# page for editing the scenarios
@app.route('/scenarios', defaults={'error': None})
def scenarios(error):
    return render_template("scenarios.html", scenarios=get_scenario_list(), error=error)


@app.route('/scenario_error', defaults={'error': 'There was an error.'})
@app.route('/scenario_<error>')
def scenario_error(error):
    log_error(error)
    return render_template("scenarios.html", scenarios=get_scenario_list(), error=error)


# function to check whether the uploaded file is a type of file that can be accepted by the application
def file_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# function to clean input names
def is_allowed_string(string):
    return True


# accepts an uploaded file and parses it into a new scenario with a name, description, and esps
@app.route('/upload_new_scenario', methods=['POST'])
def upload_new_scenario():
    if request.method == 'POST':
        file = request.files['file']
        data = json.loads(request.form['data'])
        name = data['name']
        schema = data['schema']
        description = data['description']
        doctype = data['docType']
        if len(doctype) < 3:
            doctype = '000'
        fulfillmenttype = data['fulfillmentType']
        print(schema)
        print(fulfillmenttype)
        error = ''
        input_data = []
        equal_esps_list = []
        is_valid = False
        filename = ''
        if file:
            if file_allowed(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                input_data, equal_esps_list, qualified_rep_dict = parser.Parser.scenario_parse(
                    app.config['UPLOAD_FOLDER'] + '/' + filename)
                if isinstance(input_data, list):
                    is_valid = True
                else:
                    error = "The file %s could not be parsed." % file.filename
            else:
                error += "File type must be .xml or .txt."
        else:
            error = "Please upload a file to create this scenario."
        if is_valid:
            esps = input_data
            result = scenarioList.ScenarioList.build_scenario(name, description, doctype, esps,
                                                              equal_esps_list, qualified_rep_dict)
            if isinstance(result, list):
                error = "The scores for some ESPs were automatically adjusted to be within the range 1 through 5."
            elif isinstance(result, bool) and result:
                flash("Scenario: %s successfully created." % name)
            else:
                error = "That name is in use. Please choose another."
        if len(error) < 1:
            return json.dumps(scenarioList.ScenarioList.get_list())
        else:
            response = make_response(error, 400)
            return response


# accepts just a name and description for a new blank scenario
@app.route('/create_scenario', methods=['POST'])
def create_scenario():
    if request.method == 'POST':
        error = ""
        name = request.json['name']
        description = request.json['description']
        doctype = request.json['docType']
        success = scenarioList.ScenarioList.build_scenario(name, description, doctype, [], [], [])
        if not success:
            error += "The name %s is taken. Please choose another name." % name
        if len(error) < 1:
            flash("Scenario %s was created successfully." % name)
            return json.dumps(scenarioList.ScenarioList.get_list())
        else:
            response = make_response(error, 400)
            return response


# deletes a scenario if it exists
@app.route('/delete_scenario', methods=['POST'])
def delete_scenario():
    error = ''
    if request.method == 'POST':
        name = request.json['name']
        success = scenarioList.ScenarioList.delete_scenario(name)
        if not success:
            error = "Scenario %s does not exist" % name
        if len(error) < 1:
            flash("Scenario %s was successfully deleted." % name)
            return json.dumps(scenarioList.ScenarioList.get_list())
        else:
            response = make_response(error, 400)
            return response


# makes a copy of a scenario that already exists
@app.route('/copy_scenario', methods=['POST'])
def copy_scenario():
    if request.method == 'POST':
        error = ''
        name_of_old_scen = request.json['oldName']
        name_of_new_scen = request.json['newName']
        descr_of_new_scen = request.json['newDescription']
        if len(name_of_old_scen) > 0 and len(name_of_new_scen) > 0:
            result = scenarioList.ScenarioList.copy_scenario(name_of_old_scen, name_of_new_scen, descr_of_new_scen)
            if not isinstance(result, bool):
                error = result
        else:
            error = "The name of the scenario to copy and the name of the new scenario must be specified."
        if len(error) < 1:
            flash("Scenario %s was successfully copied as %s." % (name_of_old_scen, name_of_new_scen))
            return json.dumps(scenarioList.ScenarioList.get_list())
        else:
            response = make_response(error, 400)
            return response


# renames a scenario that already exists
@app.route('/edit_scenario', methods=['POST'])
def edit_scenario():
    if request.method == 'POST':
        error = ''
        new_name = request.json['updatedName']
        old_name = request.json['oldName']
        result = scenarioList.ScenarioList.rename_scenario(old_name, new_name)
        if not isinstance(result, bool):
            error = result
        if len(error) < 1:
            flash("Scenario %s was successfully renamed to %s." % (old_name, new_name))
            return json.dumps(scenarioList.ScenarioList.get_list())
        else:
            response = make_response(error, 400)
            return response


# adds a single given esp to a specified scenario
@app.route('/add_esp', methods=['POST'])
def add_esp():
    if request.method == 'POST':
        error = ""
        scenName = request.json['scenName']
        xpath = request.json['xpath']
        score = request.json['score']  # is an int
        data = ''
        if 'data' in request.json:
            data = request.json['data']
        score_ok = False
        try:
            parse_score = int(score)
            score_ok = True
        except ValueError:
            error = "Score must be an integer between 1 and 5."
        if score_ok:
            if int(parse_score) > 5 or int(parse_score) < 1:
                error = "Score must be an integer between 1 and 5. Could not add ESP."
            else:
                success = models.Scenario.public_add_esp(scenName, xpath, score, data)
                if not success:
                    error = "Unable to add esp."
        if len(error) < 1:
            flash("%s was successfully added to %s." % (xpath, scenName))
            return Response(refresh_esp_list(scenName), mimetype='application/json')
        else:
            response = make_response(error, 400)
            return response


# removes one esp from a particular scenario
@app.route('/remove_esp', methods=['POST'])
def remove_esp():
    if request.method == 'POST':
        error = ""
        name = request.json['scenName']
        xpath = request.json['xpath']
        data = request.json['data']
        score = request.json['score']
        quals = []
        if 'where' in xpath:
            quals = re.sub("is", "", xpath.split(" where ")[-1])
            xpath = re.sub(" where (.*)", "", xpath)
            quals = quals.split()
        success = models.Scenario.public_remove_esp(name, xpath, data, score, quals)
        if not success:
            error = "Unable to remove esp."
        if len(error) < 1:
            flash("%s was successfully removed from %s." % (xpath, name))
            return Response(refresh_esp_list(name), mimetype='application/json')
        else:
            response = make_response(error, 400)
            return response


# removes one esp from a particular scenario
@app.route('/edit_esp', methods=['POST'])
def edit_esp():
    if request.method == 'POST':
        # print(request.json)
        error = ""
        name = request.json['scenName']
        old_xpath = request.json['oldXpath']
        old_data = request.json['oldData']
        old_score = request.json['oldScore']
        quals = []
        try:
            xpath = request.json['newXpath']
        except KeyError:
            xpath = old_xpath
        try:
            data = request.json['newData']
        except KeyError:
            data = old_data
        try:
            score = request.json['newScore']
        except KeyError:
            score = old_score
        if len(xpath) < 1:
            xpath = old_xpath
        if len(data) < 1:
            data = old_data
        if score is None:
            score = old_score
        if 'where' in old_xpath:
            quals = re.sub("is", "", old_xpath.split(" where ")[-1])
            old_xpath = re.sub(" where (.*)", "", xpath)
            quals = quals.split()
        # print("%s:%s:%s:%s:%s:%s:%s" % (name, old_xpath, old_data, str(old_score), xpath, data, str(score)))
        success = models.Scenario.edit_esp(name, old_xpath, old_data, old_score, xpath, data, score, quals)
        if not success:
            error = "Unable to edit esp."
        if len(error) < 1:
            flash("%s was successfully edited." % (xpath))
            return Response(refresh_esp_list(name), mimetype='application/json')
        else:
            response = make_response(error, 400)
            return response


# returns a list of esps if successful, else returns the webpage with a message.
@app.route('/get_esps', methods=['POST'])
def get_esps():
    if request.method == 'POST':
        error = ""
        name = request.json['name']
        exists = models.Scenario.check_exists(name)

        if exists:
            scen = models.Scenario.get_scenario(name)
            scen_esps = scen.get_esps_as_list()
            return Response(refresh_esp_list(name), mimetype='application/json')
        else:
            error = "That scenario does not exist."
        if len(error) < 1:
            return Response(refresh_esp_list(name), mimetype='application/json')
        else:
            response = make_response(error, 400)
            return response


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
        list_has_things = False
        selected_list = ''
        try:
            selected_list = request.json['name']
            if len(selected_list) > 0:
                list_has_things = True
        except KeyError:
            list_has_things = False
        if list_has_things:
            down_file = output.Output.get_scenario_as_xml_tree(selected_list)
            schema_name = 'OrderAcks'
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
        else:
            error = "Please select a Scenario for which you would a list of xpaths."
            response = make_response(error, 400)
            return response


def record_usage(processing_time, err, misc):
    app_id = int(models.get_app(app.config['APP_NAME']).id)
    models.add_info(app_id, request.environ.get('HTTP_X_REAL_IP', request.remote_addr), processing_time, err, misc)


# returns a list of esps if successful, else returns the webpage with a message.
def refresh_esp_list(name):
    exists = models.Scenario.check_exists(name)
    if exists:
        scen = models.Scenario.get_scenario(name)
        scen_esps = scen.get_esps_as_list()
        return json.dumps(scen_esps)


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
        error = ''
        if file:
            # if this is empty, schema was successfully added
            error = schemaValidation.validate.add_schema(file, schema_name)
        else:
            error = "A schema must be upload."
    if len(error) > 0:
        return make_response(error, 400)
    return get_schema_list()


@app.route('/delete_schema', methods=['POST'])
def delete_schema():
    filename = request.json['delete']
    # if this is empty, schema was successfully deleted
    error = schemaValidation.validate.delete_schema(filename)
    if len(error) > 0:
        return make_response(error, 400)
    return get_schema_list()
