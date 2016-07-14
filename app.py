# main application for Cuttlefish

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

    data = graph.data("MATCH (a) RETURN a")

    return render_template("index.html",data=data[0])

#add new assets / items
@app.route('/tx', methods=['POST'])
def tx():
    owner = request.form['owner']
    model = request.form['model']

    statement = "MERGE (asset:Asset {model:{model}}) MERGE (owner:Person {name:{owner}}) MERGE (owner)-[:OWNS]->(asset)"
    graph.run(statement, model=model, owner=owner)

    paragraph = "Hello " + owner + ", here is your " + model
    return render_template('results.html',paragraph=paragraph)


@app.route('/api/return/person/<person>',methods=['POST','GET'])
def returnPerson(person):

    statement = "MATCH (a {name:{person}}) RETURN a"
    data = graph.data(statement,person=person)[0]['a']

    return str(data)

#=====#
# RUN #
#=====#

if __name__ == "__main__":
    app.run()
