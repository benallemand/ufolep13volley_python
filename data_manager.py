# coding=latin-1
import environment
import csv

if environment.environment is "DEV":
    pass
elif environment.environment is "PROD":
    pass
else:
    raise EnvironmentError("Environnement inconnu")


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
