from lxml import etree
import xml.etree.ElementTree
import re
#Compare class' only purpose is to hold the method that compares a dict of lists from input (key is xpath of the node, value is list of text from the node, where each node with the same path will put its text into the list) to a list of esps from the actual scenario that we're comparing
#from a scenario in the database

class Compare:
    
    #returns a list of the esps that aren't in the input, along with the sum of the scores for those missing fields
    #and the total sum of the scores in that scenario
    # check_data is a boolean that tells whether or not to check the data contained in the input against required data in
    # the scenario
    @staticmethod
    def compare(input_list, scenario_esp_list, tree, check_data):
        failed_check_list = []
        score = 0
        possible_score = 0
        root = tree.getroot()
        esps = scenario_esp_list[::1]
        skips = []
        #for x in input_list:
        #    print(x)
        for esp_ in esps:
            #print('top '+esp_.xpath+ ' ' +str(possible_score))
            if esp_ in skips:
                continue
            #print(esp_.xpath)
            #if multiple fields can fulfill the same role, such as BPN/UPC/VPN, check for them
            if esp_.has_equals() or esp_.is_qualifier():
                if esp_.has_equals():
                    equals = esp_.get_equals()
                    equals.append(esp_)
                    input_groups = []
                    for group in tree.xpath('/' + Compare.get_containing_group(esp_.xpath)):
                        input_groups.append(group)
                    for g in input_groups:
                        input_has_an_equal = False
                        possible_score += esp_.score
                        #print('equivalent '+esp_.xpath+ ' ' +str(possible_score))
                        for equal in equals:
                            if g.find(Compare.get_field(equal.xpath)) is not None:
                                if check_data and (esp_.data is None or  len(esp_.data) < 1 or esp_.data in input_list[equal.xpath]):
                                    input_has_an_equal = True
                                if not check_data:
                                   input_has_an_equal = True
                        if not input_has_an_equal: #if none of the multiple equal fields were found in the input
                            failed_check_list.append(esp_.xpath + " [" + esp_.data + "]" + " " + str(esp_.score))
                            score += esp_.score
                    skips.extend(equals)

                if esp_.is_qualifier():
                    qual_children = esp_.get_qual_children()
                    other_qual = esp_.get_other_qualifiers()
                    missing_quals = []
                    parent = None
                    stop = False
                    quals_label = ''
                    quals_present_score = 0
                    for qual in other_qual:
                            quals_label += '%s=%s '%(Compare.get_field(qual.xpath), qual.data)
                    #Look for all fields in the doc that match the name of the element that is the qualifier, 
                    #such as all AddressTypeCode fields, and find one that contains the correct qualifying text
                    for leaf in tree.xpath('/' + esp_.xpath):
                        if leaf.text==esp_.data:
                            parent = leaf.getparent()
                            break
                    if parent is None:
                        missing_quals.extend(other_qual)
                        stop = True
                    if not stop:
                        #print('check_qual '+esp_.xpath+ ' ' +str(possible_score))
                        for qual in other_qual:
                            quals_present_score += qual.score
                         #   print('qual_pres '+qual.xpath+ ' ' +str(quals_present_score))
                            check_qual=parent.find(re.sub(Compare.get_containing_group(esp_.xpath)+'/', "", qual.xpath))
                          #  print(esp_.xpath + " qual " + qual.xpath + " " + str(check_qual))
                            if check_qual is None or check_qual.text!=qual.data:
                                missing_quals.append(qual)
                                stop = True
                        if not stop:
                            possible_score += quals_present_score
                            for child in qual_children:
                                if not child.is_qualifier():
                                    possible_score+=child.score
                           #         print('child '+child.xpath+ ' ' +str(possible_score))
                                    if parent.find(re.sub(Compare.get_containing_group(esp_.xpath)+'/', "", child.xpath)) is None:
                                        field = ("%s Rep [%s] is missing field %s %s %s" % (Compare.get_containing_group(esp_.xpath), quals_label,  child.xpath, "" if len(child.data) < 1 else "[%s]"%child.data, str(child.score)))
                                        failed_check_list.append(field)
                                        score += child.score
                    if stop:
                        qual_group = Compare.get_containing_group(esp_.xpath)
                        group_score = 0
                        for qual in other_qual:
                            group_score += qual.score
                            #print('stop qual '+qual.xpath+ ' ' +str(group_score))
                        for child in qual_children:
                            if not child.is_qualifier():
                                group_score += child.score
                                #print('stop child '+child.xpath+ ' ' +str(group_score))
                        field = ("Missing qualified repetition: %s where %s %s" %  (qual_group, quals_label, group_score)) 
                        failed_check_list.append(field)
                        score += group_score
                        possible_score += group_score
                        
            else:
                possible_score += esp_.score
                #print('bottom '+esp_.xpath+ ' ' +str(possible_score))
                if esp_.xpath not in input_list.keys():
                    failed_check_list.append(esp_.xpath + " " + str(esp_.score))
                    score += esp_.score
                else: #if the node is in the input
                    #if the there is required data for that field, but that field in the input doesn't have the correct data
                    if check_data and (esp_.data is not None and len(esp_.data) > 0 and esp_.data not in input_list[esp_.xpath]):
                        failed_check_list.append(esp_.xpath + " [" + esp_.data + "]" + " " + str(esp_.score))
                        score += esp_.score
        return failed_check_list, score, possible_score

    def get_field(xpath):
        if '/' in xpath:
            return xpath.split('/')[-1]
        else:
            return xpath

    def get_containing_group(xpath):
        if '/' in xpath:
           group_path = re.sub('/'+Compare.get_field(xpath),"", xpath)
           return group_path
        else:
           return xpath
