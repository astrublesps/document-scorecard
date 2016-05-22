from app import app, schemaCreation, schemasLayout


class order:

    @staticmethod
    def order_xml(_file, schema):
        print(_file)
        print(schema)
        if _file and schema:
            xsd = app.config['SCHEMA_FOLDER']+'/'+schema+'.xsd'
            print(xsd)
            configure_xsd = True  # schemaCreation.create.configure_xsd(xsd)
            if configure_xsd:
                create_schema = True  # schemaCreation.create.create_schema(xsd)
                if create_schema:
                    return order.print_xml(_file)
        return False

    @staticmethod
    def print_xml(xmlfile):
        doc = schemasLayout.parsexml_(xmlfile, None)
        rootNode = doc.getroot()
        rootTag, rootClass = schemasLayout.get_root_tag(rootNode)
        if rootClass is None:
            rootTag = 'schema'
            rootClass = schemasLayout.supermod.schemasLayout
        rootObj = rootClass.factory()
        rootObj.build(rootNode)
        w = open(app.config['APP_FOLDER']+'/output.xml', 'w')
        rootObj.export(w, 0, name_=rootTag, namespacedef_='', pretty_print=True)
        w.close()
        return True
