# coding=latin-1
import os

import environment
import csv

if environment.environment is "DEV":
    pass
elif environment.environment is "PROD":
    pass
else:
    raise EnvironmentError("Unknown environment")


def get_listing_volley_licences():
    licences = []
    csv_file = open('listing volley.csv', 'rb')
    file_reader = csv.DictReader(csv_file, delimiter=';')
    for row in file_reader:
        licences.append({
            'licence_number': row['Id_Pp'],
            'activation_date': row['Date_Homologation']
        })
        # licences.append("'%s'" % row['Id_Pp'])
    return licences


def remove_photo(path_photo=None):
    """
    FTP Connect to web server and remove file in args
    :param path_photo: file to be removed
    """
    if environment.environment is "DEV":
        web_path = "C:\workspace_phpstorm\ufolep13volley"
    else:
        web_path = "~/www"
    if os.path.exists(os.path.join(web_path, path_photo)):
        print "Removing file %s..." % path_photo
        os.remove(os.path.join(web_path, path_photo))
        print "File %s removed" % path_photo
    else:
        print "Skipping file %s, it does not exist..." % path_photo
