import csv
from datetime import timedelta

import dateparser
import requests


def extract_value(pos):
    try:
        value = row[pos]
    except:
        value = None
    return value


def get_date(string, offset=0):
    date_string = None
    t = timedelta(days=offset * 365)
    p = dateparser.parse(string)
    if p:
        p = p + t
        date_string = p.strftime('%d/%m/%Y')
    return date_string


with open('/tmp/laptops.csv', 'rb') as csvfile:
    last_name = 'Unknown'
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        name = extract_value(0)
        if name:
            last_name = name
        else:
            name = last_name
        date = extract_value(1)
        serial = extract_value(2)
        details = extract_value(3)
        print get_date(date)
        print get_date(date, 2)
        if name and date and serial:
            print "{} {} {} {}".format(name, date, serial, details)
            payload = dict(owner=name, serial=serial, date_issued=get_date(date), date_renewal=get_date(date, 2))
            print payload
            r = requests.post("http://api:secret@localhost:5000/api/add/asset",
                              data=payload)
            print r.reason
            print r.status_code

