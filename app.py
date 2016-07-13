# main application for Cuttlefish


#=========#
# MODULES #
#=========#

from flask import Flask, render_template, url_for, request
from py2neo import Graph # v2.0.8

app = Flask(__name__)

#database connect
graph = Graph(password="origami abase squander costive")


@app.route('/')
def index():

    graph.run("MATCH (a) return a")

    return render_template("index.html",data="This is data")

@app.route('/tx', methods=['POST'])
def tx():
    owner = request.form['owner']
    model = request.form['model']

    statement = "MERGE (asset:Asset {model:{model}}) MERGE (owner:Person {name:{owner}}) MERGE (owner)-[:OWNS]->(asset)"
    graph.data(statement, model=model, owner=owner)

    return render_template('results.html',owner=owner, model=model)

if __name__ == "__main__":
    app.run()
