import os
from lxml import etree
import re
import time
from app import app


class create:
    @staticmethod
    def remove_empty_lines(txt):
        return '\n'.join([x for x in txt.split("\n") if x.strip() != ''])

    @staticmethod
    def configure_xsd(xsd):
        REGEX = {'<xs:enumeration>.+?</xs:enumeration>': '', '<xs:annotation>.+?</xs:annotation>': '',
                 '<xs:simpleType>.+?</xs:simpleType>': '', 'type="xs:.+?"': 'type="attributes-string"'}
        f = open(xsd, 'r+')
        file_string = f.read()
        f.close()
        for regex, replacement in REGEX.items():
            s = re.compile(regex, re.DOTALL)
            file_string = re.sub(s, replacement, file_string)
        file_string = create.remove_empty_lines(file_string)
        # add_attributes()
        file_string = re.sub('</xs:schema>', create.add_attributes() + '\n</xs:schema>', file_string)
        w = open(xsd, 'w')
        w.write(file_string)
        w.close()
        return True

    @staticmethod
    def add_attributes():
        attribs = ''
        ATTRIBUTE_TYPES = {'string'}
        # Possibilities of expanding to be able to validate types
        # ATTRIBUTE_TYPES = {'integer', 'string', 'date', 'decimal', 'boolean', 'date', 'time'}
        ATTRIBUTES = {'score': 'int', 'qualified-rep': 'string', 'requires-one': 'string', 'not-equal': 'string',
                      'requires-others': 'string'}
        for attribtypes in ATTRIBUTE_TYPES:
            attribs = '<xs:complexType name="attributes-%s">\n<xs:simpleContent>\n<xs:extension base="xs:%s">\n' \
                      % (attribtypes, attribtypes)
            for attribute, Att_type in ATTRIBUTES.items():
                attribs += '<xs:attribute name="%s" type="xs:%s"' % (attribute, Att_type)
                if attribute == 'score':
                    attribs += ' use="required"'
                attribs += '/> \n'
            attribs += '</xs:extension>\n</xs:simpleContent>\n</xs:complexType>'
        # print(attribs)
        # print("add_attributes--- %s seconds ---" % (time.time() - start_time))
        return attribs

    @staticmethod
    def create_schema(xsd):
        schema = etree.parse(xsd)
        schema.write(xsd)  # This needs to be done only one time when the file is first uploaded
        # root = schema.getroot()
        # string_o = root[0].attrib['name']
        # string_s = root[1].attrib['name']
        string_o = 'schemasLayout'
        string_s = 'schema'
        _object = '%s/%s.py' % (app.config['APP_FOLDER'], string_o)
        sub_object = '%s.py' % string_s
        _super = string_o
        xsd_name = xsd
        generateDS_path = app.config['GENERATEDS_FOLDER']
        print('creating schema')
        os.system('python %s/generateDS.py -f -o %s %s'
                  % (generateDS_path, _object, xsd_name))
        # os.system('python ..\generateDS-2.22a0\generateDS.py -f -o %s -s %s --super="%s" %s'
        #           % (_object, sub_object, _super, xsd_name))
        return True
