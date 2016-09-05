# Cuttlefish CMDB
# Configuration Management Database leveraging Neo4j

# =======#
# LEGAL #
# =======#

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


# =========#
# MODULES #
# =========#

import time
from functools import wraps
from uuid import uuid4

import apiclient
import httplib2
import os
from flask import Flask, render_template, url_for, request, redirect, session, abort, flash, Response, jsonify
from flask_httpauth import HTTPBasicAuth
from oauth2client import client
from parseXML import parseXML
from py2neo import Graph
from werkzeug.utils import secure_filename

DATE_FORMAT = '%d/%m/%Y'

AUTH_REQUIRED = 2

app = Flask(__name__)
app.debug = True
app.secret_key = os.environ['APP_SECRET']  # for sessions
app.config['UPLOAD_FOLDER'] = '/uploads'

DEFAULT_NEO_URL = 'http://neo4j:secret@localhost:7474'
graph = Graph(os.environ.get('GRAPHSTORY_URL', DEFAULT_NEO_URL), bolt=False)

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'xml'}
TWO_WEEKS = 1209600
basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
    return username == os.environ['API_USER'] and password == os.environ['API_PASSWORD']

def google_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'CLIENT_ID' in os.environ:
            if 'username' not in session:
                return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def create_indexes():
    constraint_statements = [
        # "CREATE CONSTRAINT ON (asset:Asset) ASSERT asset.mac IS UNIQUE;",
        "CREATE CONSTRAINT ON (asset:Asset) ASSERT asset.serial IS UNIQUE;",
        # "CREATE CONSTRAINT ON (ip:Ip) ASSERT ip.address IS UNIQUE;",
        "CREATE CONSTRAINT ON (owner:Person) ASSERT owner.name IS UNIQUE"]

    for constraint_statement in constraint_statements:
        graph.run(constraint_statement)


@app.route('/')
@google_login
def index():
    assets = graph.data(
        """MATCH (asset:Asset)
        OPTIONAL MATCH (asset)-[:HAS_IP]->(ip:Ip)
        OPTIONAL MATCH (owner:Person)-[:OWNS]->(asset)
        RETURN asset, owner, ip, id(asset) AS iid""")

    for row in assets:
        asset = row['asset']
        date_issued = asset['date_issued']
        if date_issued is not None:
            asset['date_issued'] = get_local_date(date_issued)

        date_renewal = asset['date_renewal']
        if date_renewal is not None:
            asset['date_renewal'] = get_local_date(date_renewal)

    renewals = get_renewals()
    outdated_assets = len(renewals)
    if outdated_assets > 0:
        flash('There are {} assets due for renewal'.format(outdated_assets))

    session.pop('upload_data', None)  # make sure session upload data is clear

    return render_template("index.html", title="Asset Data", data=assets, username=get_username())


def get_local_date(epoch_date):
    return time.strftime(DATE_FORMAT, time.gmtime(int(epoch_date)))


def get_username():
    return session['username'] if 'username' in session else 'Local User'


def parse_time(string):
    return int(time.mktime(time.strptime(string, DATE_FORMAT)))


@app.route('/login')
def login():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))

    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))

    else:
        http_auth = credentials.authorize(httplib2.Http())

        plus_service = apiclient.discovery.build('plus', 'v1', http=http_auth)
        profile = plus_service.people().get(userId='me').execute()

        if 'domain' in profile and profile['domain'] == os.environ['RESTRICTED_DOMAIN']:
            session['username'] = profile['displayName']
            session['email'] = profile['emails'][0]['value']

            return redirect(url_for('index'))

        else:
            return abort(401)


@app.route('/oauth2callback', methods=['GET', 'POST'])
def oauth2callback():
    flow = client.OAuth2WebServerFlow(
        os.environ['CLIENT_ID'],
        os.environ['CLIENT_SECRET'],
        scope='https://www.googleapis.com/auth/plus.login https://www.googleapis.com/auth/plus.profile.emails.read',
        redirect_uri=os.environ['REDIRECT_URI'],
        token_uri=os.environ['TOKEN_URI'],
        auth_provider_x509_cert_url=os.environ['AUTH_PROVIDER_X509_CERT_URL']
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
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('index'))


def get_parameter_value(req, name):
    form = req.form
    if form.has_key(name):
        return form[name]
    else:
        return "Unknown"

@app.route('/api/v1/asset/new', methods=['POST'])
@basic_auth.login_required
def add_asset_from_api_and_return_json():
    add_asset_implementation()
    return jsonify({'message':'OK'})

@app.route('/api/add/asset', methods=['POST'])
@google_login
def add_asset_and_return_html():
    add_asset_implementation()
    return redirect("/")


def add_asset_implementation():
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
                    notes:{notes},
                    state:{state}
                    })

                FOREACH(x IN (CASE WHEN {ip} IS NULL THEN [] ELSE [''] END) |
                    MERGE (ip:Ip {address:{ip}})
                    MERGE  (asset)-[:HAS_IP]->(ip)
                )

                MERGE    (owner:Person {name:{owner}})
                MERGE    (owner)-[:OWNS]->(asset)"""
    graph.run(statement,
              uid=(str(uuid4())),
              model=(get_parameter_value(request, 'model')),
              make=(get_parameter_value(request, 'make')),
              serial=(get_parameter_value(request, 'serial')),
              ip=(get_parameter_value(request, 'ip')),
              mac=(get_parameter_value(request, 'mac')),
              date_issued=parse_time(get_parameter_value(request, 'date_issued')),
              date_renewal=parse_time(get_parameter_value(request, 'date_renewal')),
              condition=(get_parameter_value(request, 'condition')),
              location=(get_parameter_value(request, 'location')),
              owner=(get_parameter_value(request, 'owner')),
              notes=(get_parameter_value(request, 'notes')),
              state=get_parameter_value(request, 'state'))


# UPDATE

@app.route('/api/update/asset/', methods=['POST'])
@google_login
def update_asset():
    form = request.form
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
                SET asset.state={state}

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
              uid=(form['uid']),
              model=(form['model']),
              make=(form['make']),
              serial=(form['serial']),
              ip=(form['ip']),
              mac=(form['mac']),
              date_issued=parse_time(form['date_issued']),
              date_renewal=parse_time(form['date_renewal']),
              condition=(form['condition']),
              owner=(form['owner']),
              location=(form['location']),
              notes=(form['notes']),
              state=(form['state']))

    return redirect(url_for('index'))


@app.route('/api/delete/asset/<uid>', methods=['GET'])
@google_login
def assetDeleteByUID(uid):
    statement = "MATCH (asset:Asset {uid:{uid}}) DETACH DELETE asset"
    graph.run(statement, uid=uid)

    return redirect("/")


@app.route('/renewals')
@google_login
def renewals():
    data = get_renewals()

    for row in data:
        issued_ = int(row['asset']['date_issued'])
        renewal_ = int(row['asset']['date_renewal'])
        row['asset']['date_issued'] = get_local_date(issued_)
        row['asset']['date_renewal'] = get_local_date(renewal_)

    return render_template("index.html", title="New Renewals", data=data, username=get_username())


def get_renewals():
    statement = """
                MATCH (asset:Asset)
                WHERE (asset.date_renewal - 121000000.0) < (timestamp() / 1000.0) and asset.state = 'ASSIGNED'
                WITH asset
                OPTIONAL MATCH (asset)-[:HAS_IP]->(ip:Ip)
                OPTIONAL MATCH (owner:Person)-[:OWNS]->(asset)
                RETURN asset, owner, ip, id(asset) AS iid
                """
    try:
        data = graph.data(statement)
    except ValueError:
        pass
    return data


@app.route('/api/upload', methods=['GET', 'POST'])
@google_login
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
        session.pop('upload_data', None)  # clears upload data

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

            data = parseXML(os.path.join('uploads', filename))
            session['upload_data'] = data

            os.remove(os.path.join('uploads', filename))

        return render_template("upload.html", data=data, username=get_username())

    return abort(400)


@app.route('/api/upload/clear')
@google_login
def uploadClear():
    session.pop('upload_data', None)
    return redirect(url_for('index'))


@app.route('/api/cleanup')
@google_login
def cleanup():
    # gets rid of owners or
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


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=(int(os.environ.get('PORT', 33507))))
    create_indexes()
    app.run()
