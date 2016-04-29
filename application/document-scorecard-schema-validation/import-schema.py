import os
from lxml import etree
import re
import time

# the last regex (type=...) is causing issues, we do not need to remove it right now
# REGEX = {'<xs:enumeration>.+?</xs:enumeration>', '<xs:annotation>.+?</xs:annotation>',
#          '<xs:simpleType>.+?</xs:simpleType>', 'type=\".+?\"'}
REGEX = {'<xs:enumeration>.+?</xs:enumeration>': '', '<xs:annotation>.+?</xs:annotation>': '',
         '<xs:simpleType>.+?</xs:simpleType>': ''}  # , 'type="(.+?)"': 'type="attributes-%1"'

ATTRIBUTE_TYPES = {'integer', 'string', 'date', 'decimal', 'boolean', 'date', 'time'}
ATTRIBUTES = {'score': 'int', 'qualified-rep': 'string', 'requires-one': 'string', 'not-equal': 'string', 'requires-others': 'string'}


def remove_empty_lines(txt):
    return '\n'.join([x for x in txt.split("\n") if x.strip() != ''])


def configure_xsd(xsd):
    f = open(xsd, 'r+')
    file_string = f.read()
    f.close()

    for regex, replacement in REGEX.items():
        s = re.compile(regex, re.DOTALL)
        file_string = re.sub(regex, replacement, file_string)

    file_string = remove_empty_lines(file_string)

    # add_attributes()
    # file_string = re.sub('</xs:schema>', add_attributes()+'\n</xs:schema>', file_string)

    w = open(xsd, 'w')
    w.write(file_string)
    w.close()


def add_attributes():

    for attribtypes in ATTRIBUTE_TYPES:
        attribs = '<xs:complexType name = "attributes-%s">\n<xs:simpleContent>\n<xs:extension base = "xs:%s">\n' \
                  % (attribtypes, attribtypes)

        for attribute, Att_type in ATTRIBUTES.items():
            attribs += '<xs:attribute name = "%s" type = "xs:%s"' % (attribute, Att_type)

            if attribute == 'score':
                attribs += ' use="required"'

            attribs += '> \n'

        attribs += '</xs:extension>\n</xs:simpleContent>\n</xs:complexType>'

    print(attribs)
    return attribs


def create_schema():
    schema = etree.parse(xsd)
    schema.write(xsd)  # This needs to be done only one time when the file is first uploaded
    root = schema.getroot()

    string_o = root[0].attrib['name']
    string_s = root[1].attrib['name']
    _object = '%s.py' % string_o
    sub_object = '%s.py' % string_s
    _super = string_o
    xsd_name = xsd

    os.system('python ..\generateDS-2.22a0\generateDS.py -f -o %s -s %s --super="%s" %s'
              % (_object, sub_object, _super, xsd_name))


def print_xml():
    # Invoice.parse('7.6.3_Invoices.xml')
    # ItemRegistry.parse('7.6.3_ItemRegistries.xml')
    # Order.parse('7.6.3_Orders.xml')
    # OrderAck.parse('7.6.3_OrderAcks.xml')
    # OrderChange.parse('7.6.3_OrderChanges.xml')
    # Shipment.parse('7.6.3_Shipments.xml')

    w = open('output.xml', 'w')
    # strvar = Invoice.parse('7.6.3_Invoices.xml', silence=True)
    Invoices.parse('7.6.3_Invoices.xml')
    # ItemRegistry.parse('7.6.3_ItemRegistries.xml')
    # Order.parse('7.6.3_Orders.xml')
    # OrderAck.parse('7.6.3_OrderAcks.xml')
    # OrderChange.parse('7.6.3_OrderChanges.xml')
    # Shipment.parse('7.6.3_Shipments.xml')
    # root = strvar.get_root_tag()
    # print(root)
    # w.write(str(strvar))

    # w.write(ItemRegistry.parse('7.6.3_ItemRegistriesS.xml'))
    # w.write(Order.parse('7.6.3_Orders.xml'))
    # w.write(OrderAck.parse('7.6.3_OrderAcks.xml'))
    # w.write(OrderChange.parse('7.6.3_OrderChanges.xml'))
    # w.write(Shipment.parse('7.6.3_Shipments.xml'))
    # w.close()

xsd = 'xsd/Invoices.xsd'
# xsd = 'xsd/ItemRegistries.xsd'
# xsd = 'xsd/Orders.xsd'
# xsd = 'xsd/OrderAcks.xsd'
# xsd = 'xsd/OrderChanges.xsd'
# xsd = 'xsd/Shipments.xsd'


start_time = time.time()
print("--- %s seconds ---" % (time.time() - start_time))

configure_xsd(xsd)
print("--- %s seconds ---" % (time.time() - start_time))

add_attributes()

create_schema()
print("--- %s seconds ---" % (time.time() - start_time))

import Invoices
# import ItemRegistry
# import Order
# import OrderAck
# import OrderChange
# import Shipment

print_xml()
print("--- %s seconds ---" % (time.time() - start_time))