# Cuttlefish CMDB
# Configuration Management Database leveraging Neo4j
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

from flask import Flask, render_template, url_for, request
from py2neo import Graph # v2.0.8

#======#
# MAIN #
#======#

app = Flask(__name__)

#database connect
graph = Graph(password="origami abase squander costive")

#index
@app.route('/')
def index():

    data = graph.data("MATCH (b:Person)-[:OWNS]->(a:Asset) RETURN a AS asset, b AS person")

    return render_template("index.html",data=data)

#add new assets / items
@app.route('/api/add/asset', methods=['POST'])
def assetAdd():

    localaize data
    internalID = request.form['internalID']
    model = request.form['model']
    serial = request.form['serial']
    make = request.form['make']
    ip = request.form['ip']
    mac = request.form['mac']
    date_issued = request.form['date_issued']
    date_renewel = request.form['date_renewel']
    condition = request.form['condition']
    owner = request.form['owner']
    location = request.form['location']

    statement = "MERGE (asset:Asset {model:{model}}) MERGE (owner:Person {name:{owner}}) MERGE (owner)-[:OWNS]->(asset)"
    graph.run(statement, model=model, owner=owner)

    paragraph = "Hello " + owner + ", here is your " + model
    return render_template('results.html',paragraph=paragraph)

@app.route('/api/return/person/<person>',methods=['GET'])
def returnPerson(person):

    statement = "MATCH (a:Person {name:{person}}) RETURN a"
    data = graph.data(statement,person=person)[0]['a']

    return str(data)

@app.route('/api/return/asset/<asset>',methods=['GET'])
def returnAsset(asset):

    statement = "MATCH (a:Asset {model:{asset}}) RETURN a"
    data = graph.data(statement,asset=asset)[0]['a']

    return str(data)

#=====#
# RUN #
#=====#

if __name__ == "__main__":
    app.run()
