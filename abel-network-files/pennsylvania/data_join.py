'''
Author: Abel Gonzalez
Date: 10/02/18

Description:
This program takes the data from the .shp file with geographic information
and .csv file with voting information and creates a dictionary with geoid of
each precint as key and geometric, voting data as value
'''
import csv
import json
import fiona


def create_dictionary(datafile):
    '''Creates the dictionary with .csv file

    Arguments:
        datafile {string} -- .csv file with path information

    Returns:
        dict -- dictionary with geoid as key and a dictionary as value
    '''
    with open(datafile) as csv_file:
        data = dict()
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for row in csv_reader:
            # To deal with long cases, if row[10] != 0.
            geoid = row[9]
            republican_vote = row[2]
            democrat_vote = row[3]
            other_vote = row[4]
            total_vote = row[5]
            data[geoid.lower()] = {
                'rep': republican_vote,
                'dem': democrat_vote,
                'oth': other_vote,
                'tot': total_vote}
        return data


def join_data(data_dict):
    '''Takes the .shp file and adds population and geomtry data

    Arguments:
        data_dict {data_dict} -- DIctionary with geoid as keys

    Returns:
        dict -- same dictionary as the input with data added.
    '''
    with fiona.open(shapefile) as shapes:
        for feat in shapes:
            try:
                properties = eval(str(feat['properties'])[7:].lower())
            except NameError:  # weird error, only happens 7 times.
                continue
            try:
                data_dict[properties['geoid10']]['pop'] = int(
                    properties['tapersons'])
                data[properties['geoid10']]['geo'] = feat['geometry']
            except KeyError:  # this error is about the long lines in the data.
                continue
    return data_dict


def save_data(data_dict):
    """saves the dictionary in a .json file

    Arguments:
        data_dict {dict} -- dictionary created on the previous functions
    """

    with open('data.json', 'w') as fp:
        json.dump(data, fp)
    return 0

datafile = ('pennsylvania/data/refined.csv')
shapefile = ('pennsylvania/data/VTDS.shp')
data = create_dictionary(datafile)
data = join_data(data)
print(len(data))
#save_data(data)

## In three ocations the data does not get updated
## which means there are geoids not in data