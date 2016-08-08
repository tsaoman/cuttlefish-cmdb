# Cuttlefish CMDB
# Configuration Management Database leveraging Neo4j

#=======#
# LEGAL #
#=======#

# Copyright (C) 2016 Brandon Tsao
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#=========#
# MODULES #
#=========#

from flask import Flask, render_template, url_for, request, redirect, session, jsonify, abort
from flask_basicauth import BasicAuth
from oauth2client import client
from py2neo import Graph
from uuid import uuid4

import os, sys, httplib2, json, apiclient, time

#=============#
# CONFIG VARS #
#=============#

AUTH_REQUIRED = 2
# RESTRICTED_DOMAIN = 'neotechnology.com'

#======#
# MAIN #
#======#

app = Flask(__name__)
app.debug = True
app.secret_key = str(os.urandom(32))

#database connect
graph = Graph(os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474'),bolt=False)

#basic auth

if AUTH_REQUIRED == 1:
    app.config['BASIC_AUTH_USERNAME'] = 'user'
    app.config['BASIC_AUTH_PASSWORD'] = 'password'
    app.config['BASIC_AUTH_FORCE'] = True
    basic_auth = BasicAuth(app)

# handling time

#==================#
# GLOBAL FUNCTIONS
#==================#


#========#
# ROUTES #
#========#

#index
@app.route('/')
def index():

    if 'username' in session:
        username = session['username']
    else:
        return redirect(url_for('login'))

    data = graph.data("MATCH (owner:Person)-[:OWNS]->(asset:Asset)-[:HAS_IP]->(ip:Ip) RETURN asset, owner, ip, id(asset) AS iid")

    #convert POSIX time to user readable
    for row in data:

        try:
            row['asset']['date_issued'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_issued'])))
            row['asset']['date_renewal'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_renewal'])))
        except:
            pass

    #return data[0]['asset']['date_issued']
    return render_template("index.html", title="Asset Data", data=data, username=username)

#auth routes

@app.route('/login')
def login():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))

    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))

    else:
        http_auth = credentials.authorize(httplib2.Http())

        plus_service = apiclient.discovery.build('plus','v1',http=http_auth)
        profile = plus_service.people().get(userId='me').execute()

        if 'domain' in profile and profile['domain'] == os.environ['RESTRICTED_DOMAIN']:
            session['username'] = profile['displayName']
            session['email'] = profile['emails'][0]['value']

            return redirect(url_for('index'))

        else:
            return abort(401)

@app.route('/oauth2callback',methods=['GET','POST'])
def oauth2callback():

    flow = client.OAuth2WebServerFlow(
        os.environ['CLIENT_ID'],
        os.environ['CLIENT_SECRET'],
        scope = 'https://www.googleapis.com/auth/plus.login https://www.googleapis.com/auth/plus.profile.emails.read',
        redirect_uri = os.environ['REDIRECT_URI'],
    )

    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('email',None)
    return redirect(url_for('index'))

#asset CRUD

#add new assets / items
@app.route('/api/add/asset', methods=['POST'])
def assetAdd():

    uid = str(uuid4())#generate uid

    #localaize data
    model = request.form['model']
    make = request.form['make']
    serial = request.form['serial']
    ip = request.form['ip']
    mac = request.form['mac']
    date_issued = request.form['date_issued']
    date_renewal = request.form['date_renewal']
    condition = request.form['condition']
    owner = request.form['owner']
    location = request.form['location']
    notes = request.form['notes']

    statement = """
                MERGE (asset:Asset {
                    uid:{uid},
                    model:{model},
                    make:{make},
                    serial:{serial},
                    mac:{mac},
                    date_issued:{date_issued},
                    date_renewal:{date_renewal},
                    condition:{condition},
                    location:{location},
                    notes:{notes}
                    })

                MERGE (ip:Ip {address:{ip}})
                MERGE (asset)-[:HAS_IP]->(ip)

                MERGE (owner:Person {name:{owner}})
                MERGE (owner)-[:OWNS]->(asset)
                """

    graph.run(statement,
                uid=uid,
                model=model,
                make=make,
                serial=serial,
                ip=ip,
                mac=mac,
                date_issued=int(time.mktime(time.strptime(date_issued,'%m/%d/%Y'))),
                date_renewal=int(time.mktime(time.strptime(date_renewal,'%m/%d/%Y'))),
                condition=condition,
                location=location,
                owner=owner,
                notes=notes)

    return redirect("/")

#UPDATE

@app.route('/api/update/asset/', methods=['POST'])
def assetUpdate():

    #locallize data
    uid = request.form['uid']
    model = request.form['model']
    make = request.form['make']
    serial = request.form['serial']
    ip = request.form['ip']
    mac = request.form['mac']
    date_issued = request.form['date_issued']
    date_renewal = request.form['date_renewal']
    condition = request.form['condition']
    owner = request.form['owner']
    location = request.form['location']
    notes = request.form['notes']

    statement = """
                MATCH (asset:Asset {uid:{uid}})

                SET asset.model={model}
                SET asset.make={make}
                SET asset.serial={serial}

                SET asset.mac={mac}
                SET asset.date_issued={date_issued}
                SET asset.date_renewal={date_renewal}
                SET asset.condition={condition}
                SET asset.location={location}
                SET asset.notes={notes}

                MERGE (ip:Ip {address:{ip}})
                WITH asset, ip
                OPTIONAL MATCH (asset)-[rip:HAS_IP]->(ip0:Ip)

                FOREACH(x IN (CASE WHEN ip <> ip0   THEN [1] ELSE [] END) |
                    DETACH DELETE rip
                    MERGE (asset)-[:HAS_IP]->(ip)
                    MERGE (asset)-[:HAS_PREVIOUS_IP]->(ip0)
                )

                MERGE (owner:Person {name:{owner}})
                WITH asset, owner
                OPTIONAL MATCH (asset)<-[rown:OWNS]-(owner0:Person)

                FOREACH(x IN (CASE WHEN owner <> owner0 THEN [1] ELSE [] END) |
                    DETACH DELETE rown
                    MERGE (asset)<-[:OWNS]-(owner)
                    MERGE (asset)<-[:PREVIOUSLY_OWNED]-(owner0)
                )
                """

    graph.run(statement,
                uid=uid,
                model=model,
                make=make,
                serial=serial,
                ip=ip,
                mac=mac,
                date_issued=int(time.mktime(time.strptime(date_issued,'%m/%d/%Y'))),
                date_renewal=int(time.mktime(time.strptime(date_renewal,'%m/%d/%Y'))),
                condition=condition,
                owner=owner,
                location=location,
                notes=notes)

    return redirect(url_for('index'))

#delete
@app.route('/api/delete/asset/<uid>',methods=['GET'])
def assetDeleteByUID(uid):

    statement = "MATCH (asset:Asset {uid:{uid}}) DETACH DELETE asset"
    graph.run(statement, uid=uid)

    return redirect("/")

@app.route('/renewals')
def renewals():

    if 'username' in session:
        username = session['username']
    else:
        return redirect(url_for('login'))

    statement = """
                MATCH (owner:Person)-[:OWNS]->(asset:Asset)-[:HAS_IP]->(ip:Ip)
                WHERE (asset.date_renewal - 121000000.0) < (timestamp() / 1000.0)
                RETURN asset, owner, ip, id(asset) AS iid
                """
    #1.21E6 = 2 weeks
    data = graph.data(statement)

    for row in data:
        row['asset']['date_issued'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_issued'])))
        row['asset']['date_renewal'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_renewal'])))

    return render_template("index.html", title="New Renewals", data=data, username=username)

#clean
@app.route('/api/cleanup')
def cleanup():

    #gets rid of owners or
    statement = """
                MATCH (a:Owner)
                WHERE size((a)--()) = 0
                DELETE a

                MATCH (a:Ip)
                WHERE size((a)--()) = 0
                DELETE a
                """

    graph.run(statement)

    return redirect(url_for('index'))

#=====#
# RUN #
#=====#

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=(int(os.environ.get('PORT', 33507))))
    app.run()
