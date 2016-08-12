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

from flask import Flask, render_template, url_for, request, redirect, session, abort, flash
from oauth2client import client
from werkzeug.utils import secure_filename
from functools import wraps
from py2neo import Graph
from uuid import uuid4
import os
import httplib2
import apiclient
import time

from parseXML import parseXML

#=============#
# CONFIG VARS #
#=============#

AUTH_REQUIRED = 2
# RESTRICTED_DOMAIN = 'neotechnology.com'

#======#
# MAIN #
#======#

#app init
app = Flask(__name__)
app.debug = True
app.secret_key = os.environ['APP_SECRET'] #for sessions
app.config['UPLOAD_FOLDER'] = '/uploads'

#database connect
graph = Graph(os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474'),bolt=False)

#set up filesystem for uploads
UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['xml'])

#==================#
# GLOBAL FUNCTIONS #
#==================#

def loginRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#========#
# ROUTES #
#========#

#index
@app.route('/')
@loginRequired
def index():

    constraint_statement = """
                CREATE CONSTRAINT ON (asset:Asset) ASSERT asset.mac IS UNIQUE;
                CREATE CONSTRAINT ON (ip:Ip) ASSERT ip.address IS UNIQUE;
                CREATE CONSTRAINT ON (owner:Person) ASSERT owner.name IS UNIQUE
                """

    # graph.run(constraint_statement)

    data = graph.data("MATCH (owner:Person)-[:OWNS]->(asset:Asset)-[:HAS_IP]->(ip:Ip) RETURN asset, owner, ip, id(asset) AS iid")

    #convert POSIX time to user readable
    flash_flag = 0 #alert user to renweable assets
    for row in data:

        date_issued = row['asset']['date_issued']
        if date_issued is not None:
            row['asset']['date_issued'] = time.strftime("%m/%d/%Y", time.gmtime(int(date_issued)))
            if (int(date_issued) - 1.21E6) < time.time():
                flash_flag = True

        date_renewal = row['asset']['date_renewal']
        if date_renewal is not None:
            row['asset']['date_renewal'] = time.strftime("%m/%d/%Y", time.gmtime(int(date_renewal)))


    if flash_flag:
        flash('There are assets up for renewel')

    session.pop('upload_data', None) #make sure session upload data is clear

    return render_template("index.html", title="Asset Data", data=data, username=session['username'])

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
        redirect_uri=os.environ['REDIRECT_URI'],
        token_uri=os.environ['TOKEN_URI'],
        auth_provider_x509_cert_url = os.environ['AUTH_PROVIDER_X509_CERT_URL']
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
@loginRequired
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
@loginRequired
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
@loginRequired
def assetDeleteByUID(uid):

    statement = "MATCH (asset:Asset {uid:{uid}}) DETACH DELETE asset"
    graph.run(statement, uid=uid)

    return redirect("/")

@app.route('/renewals')
@loginRequired

def renewals():

    statement = """
                MATCH (owner:Person)-[:OWNS]->(asset:Asset)-[:HAS_IP]->(ip:Ip)
                WHERE (asset.date_renewal - 121000000.0) < (timestamp() / 1000.0)
                RETURN asset, owner, ip, id(asset) AS iid
                """
    #1.21E6 = 2 weeks
    try:
        data = graph.data(statement)
    except ValueError:
        pass

    for row in data:
        row['asset']['date_issued'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_issued'])))
        row['asset']['date_renewal'] = time.strftime("%m/%d/%Y", time.gmtime(int(row['asset']['date_renewal'])))

    return render_template("index.html", title="New Renewals", data=data, username=session['username'])

@app.route('/api/upload', methods=['GET','POST'])
@loginRequired
def uploadFile():

    if 'upload_data' in session:

        data = session.get('upload_data', None)

        for row in data:
            uid = str(uuid4())

            if 'mac' in row and 'ipv4' in row and row['mac']:

                statement = """
                            CREATE (asset:Asset {mac:{mac}})

                            MERGE (owner:Person {name:'unknown'})
                            MERGE (owner)-[:OWNS]->(asset)

                            MERGE (ip:Ip {address:{ip}})
                            MERGE (asset)-[:HAS_IP]->(ip)
                            """
                try:
                    graph.run(statement, uid=uid, mac=row['mac'], ip=row['ipv4'])
                except:
                    pass

        flash("File contents added to database.")
        session.pop('upload_data', None) #clears upload data

        return redirect(url_for('index'))

    if request.method == 'POST':



        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('uploads', filename))

            data = parseXML(os.path.join('uploads',filename))
            session['upload_data'] = data

            os.remove(os.path.join('uploads',filename)) #deletes file aftre grabbing data

        return render_template("upload.html", data=data, username=session['username'])

    return abort(400)

@app.route('/api/upload/clear')
@loginRequired
def uploadClear():
    session.pop('upload_data', None)
    return redirect(url_for('index'))

#clean
@app.route('/api/cleanup')
@loginRequired
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
