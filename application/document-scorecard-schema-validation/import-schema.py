import os
from lxml import etree
import re

# REGEX = {'<xs:enumeration>.+?</xs:enumeration>', '<xs:annotation>.+?</xs:annotation>',
#          '<xs:simpleType>.+?</xs:simpleType>', 'type=\".+?\"'}
REGEX = {'<xs:enumeration>.+?</xs:enumeration>', '<xs:annotation>.+?</xs:annotation>', '<xs:simpleType>.+?</xs:simpleType>', 'type=\".+?\"'}


def remove_empty_lines(txt):
    return '\n'.join([x for x in txt.split("\n") if x.strip() != ''])


def trim_xsd(xsd):
    f = open(xsd, 'r+')
    file_string = f.read()
    f.close()

    for i in REGEX:
        s = re.compile(i, re.DOTALL)
        file_string = re.sub(s, '', file_string)

    file_string = remove_empty_lines(file_string)

    w = open(xsd, 'w')
    w.write(file_string)
    w.close()


def create_schema():
    schema = etree.parse(xsd)
    schema.write(xsd) #This needs to be done only one time when the file is first uploaded
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
    Shipment.parse('7.6.3_Shipments.xml')


# xsd = 'xsd/Invoices.xsd'
# xsd = 'xsd/ItemRegistries.xsd'
# xsd = 'xsd/Orders.xsd'
# xsd = 'xsd/OrderAcks.xsd'
# xsd = 'xsd/OrderChanges.xsd'
xsd = 'xsd/Shipments.xsd'

trim_xsd(xsd)
create_schema()

import Invoice
import ItemRegistry
import Shipment
import Order
import OrderAck
import OrderChange

print_xml()
