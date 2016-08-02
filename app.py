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

import os, sys, httplib2, json, apiclient

#=============#
# CONFIG VARS #
#=============#

AUTH_REQUIRED = 2
RESTRICTED_DOMAIN = 'neotechnology.com'

#======#
# MAIN #
#======#

app = Flask(__name__)
app.debug = False
app.secret_key = str(os.urandom(32))

#database connect
graph = Graph(os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474'),bolt=False)

#auth

if AUTH_REQUIRED == 1:
    app.config['BASIC_AUTH_USERNAME'] = 'user'
    app.config['BASIC_AUTH_PASSWORD'] = 'password'
    app.config['BASIC_AUTH_FORCE'] = True
    basic_auth = BasicAuth(app)

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

    data = graph.data("MATCH (b:Person)-[:OWNS]->(a:Asset) RETURN a AS asset, b AS person, id(a) AS uid, id(b) as pid")

    return render_template("index.html",data=data,username=username)

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

        if 'domain' in profile and profile['domain'] == RESTRICTED_DOMAIN:
            session['username'] = profile['displayName']
            session['email'] = profile['emails'][0]['value']

            return redirect(url_for('index'))

        else:
            return abort(401)

@app.route('/oauth2callback',methods=['GET','POST'])
def oauth2callback():

    flow = client.flow_from_clientsecrets(
        'shadow/client_secrets.json',
        scope = 'https://www.googleapis.com/auth/plus.login https://www.googleapis.com/auth/plus.profile.emails.read',
        redirect_uri = 'http://localhost:5000/oauth2callback'
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

    #localaize data
    model = request.form['model']
    make = request.form['make']
    serial = request.form['serial']
    ip = request.form['ip']
    mac = request.form['mac']
    date_issued = request.form['date_issued']
    date_renewel = request.form['date_renewel']
    condition = request.form['condition']
    owner = request.form['owner']
    location = request.form['location']

    statement = """MERGE (asset:Asset {
                    model:{model},
                    make:{make},
                    serial:{serial},
                    ip:{ip},
                    mac:{mac},
                    date_issued:{date_issued},
                    date_renewel:{date_renewel},
                    condition:{condition},
                    location:{location}
                    })

                MERGE (owner:Person {name:{owner}})
                MERGE (owner)-[:OWNS]->(asset)"""

    graph.run(statement,
                model=model,
                make=make,
                serial=serial,
                ip=ip,
                mac=mac,
                date_issued=date_issued,
                date_renewel=date_renewel,
                condition=condition,
                location=location,
                owner=owner)

    return redirect("/")

# GET
@app.route('/api/return/person/<person>',methods=['GET'])
def returnPerson(person):

    statement = "MATCH (a:Person {name:{person}}) RETURN a AS person"
    data = graph.data(statement,person=person)[0]['person']

    return str(data)

@app.route('/api/return/asset/<asset>',methods=['GET'])
def returnAsset(asset):

    statement = "MATCH (a:Asset {model:{asset}}) RETURN a AS asset"
    data = graph.data(statement,asset=asset)[0]['asset']

    return str(data)

#UPDATE

@app.route('/api/update/asset/',methods=['POST'])
def assetUpdate():

    #locallize data
    uid = int(request.form['uid'])
    model = request.form['model']
    make = request.form['make']
    serial = request.form['serial']
    ip = request.form['ip']
    mac = request.form['mac']
    date_issued = request.form['date_issued']
    date_renewel = request.form['date_renewel']
    condition = request.form['condition']
    owner = request.form['owner']
    location = request.form['location']

    statement = """OPTIONAL MATCH (asset:Asset)-[r]-(person:Person)
                WHERE id(asset)={uid}
                delete r
                SET asset.model={model}
                SET asset.make={make}
                SET asset.serial={serial}
                SET asset.ip={ip}
                SET asset.mac={mac}
                SET asset.date_issued={date_issued}
                SET asset.date_renewel={date_renewel}
                SET asset.condition={condition}
                SET asset.location={location}
                MERGE (person:Person {name:{owner}})
                MERGE (person)-[:OWNS]->(asset)

                """

    graph.run(statement,
                uid=uid,
                model=model,
                make=make,
                serial=serial,
                ip=ip,
                mac=mac,
                date_issued=date_issued,
                date_renewel=date_renewel,
                condition=condition,
                location=location)

    return redirect("/")

#delete
@app.route('/api/delete/asset/<int:uid>',methods=['GET'])
def assetDeleteByUID(uid):

    statement = "MATCH (asset:Asset) WHERE id(asset)={uid} DETACH DELETE asset"
    graph.run(statement, uid=uid)

    return redirect("/")

#auth
@app.route('/auth/oauth2callback')
def authCallback():
    pass

#=====#
# RUN #
#=====#

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=(int(os.environ.get('PORT', 33507))))
    app.run()
