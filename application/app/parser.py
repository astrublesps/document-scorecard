from lxml.etree import XMLSyntaxError
from lxml import etree
import xml.etree.ElementTree
from app import models
import re


# Parser uses lxml to parse the xml input.
class Parser:
    esp_data_list = []
    data_tree = None

    @staticmethod
    def scenario_parse(file_name):
        error = ''

        with open(file_name) as xml_file:
            parsing = etree.XMLParser(ns_clean=True)
            try:
                Parser.data_tree = etree.parse(xml_file, parsing)

            except XMLSyntaxError:
                return '', 'There was a problem parsing %s. Please report a bug if issue cannot be resolved from the following: insert weblink to help page' % file_name

        # Parser.doc_root = Parser.data_tree.getroot()
        etree.tostring(Parser.data_tree.getroot())

        # treat nodes as nodes in a tree - only visit each node once, so that the same node doesn't get added to the scenario
        # in more than one place
        # in order to accomplish this, give each node a "visited" attribute before processing starts
        nodes = Parser.data_tree.iter()
        for n in nodes:
            attributes = n.attrib
            if attributes:
                print(attributes)
                attributes['visited'] = 'no'

        # go through all the fields in the document to check for scores, if missing or invalid - err
        nodes = Parser.data_tree.iter()
        for node in nodes:
            if len(node) < 1:  # this is a leaf node, or a field
                if 'score' in node.attrib:
                    try:
                        score = int(node.attrib['score'])
                        score_is_number = True
                    except:
                        error += '\nline %s: invalid score for %s' % (node.sourceline, node.tag)
                        score_is_number = False
                    if score < 1 or score > 5 and score_is_number:
                        error += '\nline %s: invalid score for %s' % (node.sourceline, node.tag)
                else:
                    error += '\nline %s: missing score for %s' % (node.sourceline, node.tag)

        print(error)
        if error:
            return "", error

        # if the first child node of this node is a leaf, then we have the parent of a group of leaves/fields, process this group
        nodes = Parser.data_tree.iter()
        for node in nodes:
            if len(node) > 1:
                Parser.process_node(node)

        return Parser.esp_data_list, error

    # method to check through a "parent" node from the document to see whether there are any important relationships to define
    # eg qualified repetition of a group or 2+ fields that are equivalent, such as LineItem.VPN and LineItem.BPN
    def process_node(parent_node):
        for child in parent_node.getchildren():
            if len(child) < 1:
                xpath_score_data = Parser.check_required_data(Parser.data_tree.getpath(child), child)
                Parser.esp_data_list.append(xpath_score_data)
            else:
                Parser.process_node(child)

    # helper method to take in individual fields/leaves and give back a dict with the field's xpath, score,
    # and required data
    # parameters: string xpath, string node.text
    # returns: dict
    def check_required_data(xpath, node):
        data = node.text
        path = re.sub("\[(.*)]", "", xpath)
        score = node.attrib['score']
        return {'xpath': path, 'score': score, 'data': data}

    # input_parse parses an xml file that is given as input, so it gets all the xpaths of all the nodes and checks to see
    # whether each field has data. It returns a list of all the xpaths in the input file (whether they have data or not)
    # plus a separate list of xpaths that do not have data so that can be added to the output file.
    @staticmethod
    def input_parse(file_name):
        xpath_list = {}
        empty_nodes = []
        xml = open(file_name)
        parser = etree.XMLParser(ns_clean=True)
        try:
            tree = etree.parse(xml, parser)

        except XMLSyntaxError:
            return "Error", "There was a problem parsing %s." % file_name
        xml.close()
        etree.tostring(tree.getroot())

        for node in tree.iter():
            if len(node) < 1:
                if node.text is not None:
                    xpath = re.sub("\[\d*\]", "", tree.getpath(node))
                    if xpath not in xpath_list.keys():
                        xpath_list[xpath] = [node.text]
                    else:
                        xpath_list[xpath].append(node.text)
                else:
                    empty_nodes.append(re.sub("\[\d*\]", "", tree.getpath(node)))
                    # print("input parse %s - %s" % (tree.getpath(node), node.text))
        return xpath_list, empty_nodes, tree
