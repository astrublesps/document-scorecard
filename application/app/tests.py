#!flask/bin/python
import os
import unittest

from config import basedir

from app import views, models, scenarioList, compare, parser, output




def early_test():
    test = parser.Parser.scenario_parse('app/test.xml')

    x = models.Scenario.get_list()
    for a in x:
        print(a.name)
        #models.Scenario.delete(a)
        #models.Scenario.delete_scenario(a.name)


    #models.Scenario.create_scenario('string12345678', 'description')


    scenarioList.ScenarioList.build_scenario('dropship8', 'testing of scenario_building', test)
    new = models.Scenario.get_list()
    for b in new:
        print(b)
    #esps_ = models.ESP.query.join(models.contains).all()


    data = parser.Parser.input_parse('app/input.xml')
    #for x in esps_:
    #    print(x)
    scenario = models.Scenario.get_scenario('dropship8')


    print("comparing scenario: %s " % scenario)
    esps = scenario.get_esps()
    print('starting comparison')
    xpaths, score = compare.Compare.compare(data, esps)

    #for data in esps:
      #  print(data)

    print(xpaths)
    print(score)

    output.Output.create_file("file_", xpaths, score)
