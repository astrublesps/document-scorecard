from lxml.etree import XMLSyntaxError
from lxml import etree
import xml.etree.ElementTree
from app import models
import re

#Parser uses lxml to parse the xml input.
class Parser:

    #scenario parse parses a file in order to turn it into a new scenario. The file is expected to have all the
    #required fields in it, with the score of each field in the set as the field's data
    # for example: <AddressTypeCode>4</AddressTypeCode> would be a line in the file indicating that AddressTypeCode is
    # required, and if it's not there, that's a 4-point deduction.
    @staticmethod
    def scenario_parse(file_name):
        Parser.esp_data_list = []
        Parser.equal_esps_list = []
        Parser.qualified_reps = {}
        xml = open(file_name)
        parsing = etree.XMLParser(ns_clean=True)
        try:
            Parser.tree = etree.parse(xml, parsing)

        except XMLSyntaxError:
            return "There was a problem parsing %s." % file_name
        xml.close()
        etree.tostring(Parser.tree.getroot())

        #treat nodes as nodes in a tree - only visit each node once, so that the same node doesn't get added to the scenario
        # in more than one place
        # in order to accomplish this, give each node a "visited" attribute before processing starts
        for n in Parser.tree.iter():
            attributes = n.attrib
            attributes['visited'] = 'no'

        nodes = Parser.tree.iter()
        #go through all the nodes in the tree
        for node in nodes:
            if len(node) < 1:#this is a leaf node, or a field. skip these because we want groups of fields, such as Header.Address
                x = node

            #if the first child node of this node is a leaf, then we have the parent of a group of leaves/fields. Process this group.
            elif len(node[0]) < 1:
                Parser.process_node(node)
        return Parser.esp_data_list, Parser.equal_esps_list, Parser.qualified_reps

    #method to check through a "parent" node from the XML tree to see whether there are any important relationships to define
    #eg qualified repetition of a group or 2+ fields that are equivalent, such as LineItem.VPN and LineItem.BPN
    def process_node(parent_node):
        if parent_node.attrib['visited']=='no':
            is_qualified_rep, q_index = Parser.check_qual(list(parent_node))
            has_equivalents,e_index = Parser.check_equivalents(list(parent_node))
            if is_qualified_rep and has_equivalents:#can't handle this eventuality yet
                print("both")
            elif is_qualified_rep:
                key, quals = Parser.process_qual_rep(Parser.check_required_data(Parser.tree.getpath(parent_node[q_index]), parent_node[q_index].text), parent_node[q_index].itersiblings())
                Parser.qualified_reps[key] = quals
            elif has_equivalents:
                Parser.process_equivalents(Parser.check_required_data(Parser.tree.getpath(parent_node[e_index]), parent_node[e_index].text), parent_node[e_index].itersiblings())
            else:
                for child in parent_node.getchildren():
                    if len(child) < 1:
                        if child.attrib['visited']=='no':
                            xpath_score_data = Parser.check_required_data(Parser.tree.getpath(child), child.text)
                            Parser.esp_data_list.append(xpath_score_data)
                            child.attrib['visited']='yes'
                    else:
                        Parser.process_node(child)
        parent_node.attrib['visited']='yes'

    #method checks the children/fields of a group to see if this group is a qualified repetition
    #returns boolean
    def check_qual(elements):
        for e in elements:
            if '[qualified rep]' in e.text:
                return True,e.getparent().index(e)
        return False,-1

    #method checks the children/fields of a group to see if there are any equivalent fields
    #returns boolean
    def check_equivalents(elements):
        for e in elements:
            if '%%%' in e.text:
                return True, e.getparent().index(e)
        return False,-1

    #method for getting the paths of equivalent fields and adding them to a special list to be
    #to be processed when the scenario is created
    #parameters: string xpath, list of etree nodes
    def process_equivalents(initial_xpath, siblings):
        equals = []
        regulars = []
        for sibling in siblings:
            if len(sibling) < 1:
                if '%%%' in sibling.text:
                    equal = Parser.check_required_data(Parser.tree.getpath(sibling), sibling.text)
                    Parser.equal_esps_list.append([initial_xpath, equal])
                    Parser.equal_esps_list.append([equal, initial_xpath])
                else:
                    Parser.esp_data_list.append(Parser.check_required_data(Parser.tree.getpath(sibling), sibling.text))
            else:
                Parser.process_node(sibling)
            sibling.attrib['visited']='yes'

    #method for creating a list of the required fields in a qualified repetition and a key to add the list to a dict
    #for the specific qualifier that is passed in. the key is [xpath of qualifying field] + [required qualifier data]
    # eg /Invoice/Header/Address/AddressTypeCodeST so that different qualified reps can be made from the same group type,
    # like Address where AddressTypeCode is VN and Address where AddressTypeCode is ST
    # parameters: string xpath, list of etree nodes
    #return: string key, list of fields contained and required in the qualified rep
    def process_qual_rep(first_qualifier, elements):
        first = first_qualifier
        first['is_qual']=True
        key = first['xpath'] + first['data']
        required_fields = []
        if first not in required_fields:
            required_fields.append(first)
        #elements are the siblings of the qualifier, eg if qualifier is addressTypeCode, elements would contain Address1, City, State, Zip, etc.
        for e in elements:
            if len(e) < 1:
                is_a_qualifier = False
                field = Parser.check_required_data(Parser.tree.getpath(e), e.text)
                if '[qualified rep]' in e.text:
                    is_a_qualifier = True
                field['is_qual']=is_a_qualifier
                required_fields.append(field)
            #if a qualified rep contains a nested group, process it as required within the qualified rep (nested qualifiers)
            else:
               required_fields.extend(Parser.process_qual_rep(first, e.getchildren())[1])
            e.attrib['visited']='yes'
        #print('else ' +str(required_fields))
        return key, required_fields

    #not a working method yet
    def process_qual_rep_and_equivalents(first_qualifier, siblings):
        processed = []
        group_equals = []
        first = first_qualifier
        first.append(True)
        processed.append(first)
        for sibling in siblings:
            is_a_qualifier = False
            if '%%%' or '[qualified rep]' in sibling.text:
                if '%%%' and '[qualified rep]' in sibling.text:
                    for equal in equals:
                        group_equals.append(equal)
                elif '%%%' in sibling.text:
                    x=1
                else:
                    is_a_qualifier = True
            else:
                rep_required_field = Parser.check_required_data(Parser.tree.getpath(sibling), sibling.text)
                rep_required_field['is_qual']=is_a_qualifier
                processed.append(rep_required_field)
        groups = {}
        groups['qual_fields'] = processed
        groups['equals'] = group_equals
        return groups

    #helper method to take in individual fields/leaves and give back a dict with the field's xpath, score,
    # and required data
    #parameters: string xpath, string node.text
    #returns: dict
    def check_required_data(xpath,node_text):
        esp_info = []
        data = node_text.replace('%%%','').replace('[qualified rep]','')
        path = re.sub("\[(.*)]", "", xpath)
        if '@@' in data:
            node_info = data.split('@@')
            esp_info = {'xpath': path, 'score': node_info[1], 'data': node_info[0]}
        else:
            esp_info = {'xpath': path, 'score':  data, 'data':''}
        return esp_info


    #input_parse parses an xml file that is given as input, so it gets all the xpaths of all the nodes and checks to see
    #whether each field has data. It returns a list of all the xpaths in the input file (whether they have data or not)
    #plus a separate list of xpaths that do not have data so that can be added to the output file.
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
                    xpath = re.sub("\[\d*\]","", tree.getpath(node))
                    if xpath not in xpath_list.keys():
                        xpath_list[xpath] = [node.text]
                    else:
                        xpath_list[xpath].append(node.text)
                else:
                    empty_nodes.append(re.sub("\[\d*\]", "", tree.getpath(node)))
                #print("input parse %s - %s" % (tree.getpath(node), node.text))
        return xpath_list, empty_nodes, tree
