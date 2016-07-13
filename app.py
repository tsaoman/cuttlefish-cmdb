# main application for Cuttlefish


#=========#
# MODULES #
#=========#

from flask import Flask, render_template, url_for, request
from py2neo import Graph # v2.0.8

app = Flask(__name__)

#database connect
graph = Graph()
cypher = graph.cypher
#tx = cypher.begin()

@app.route('/')
def index():

    recordList = cypher.execute("MATCH (a:Asset) return a")
    x = recordList

    return render_template("index.html", paragraph=type(recordList), x=x)

@app.route('/tx', methods=['POST'])
def tx():
    owner = request.form['owner']
    model = request.form['model']

    statement = "MERGE (asset:Asset {model:{model}}) MERGE (owner:Person {name:{owner}}) MERGE (owner)-[:OWNS]->(asset)"
    #tx.append(statement, model=model, owner=owner)
    cypher.execute(statement, model=model, owner=owner)

    # tx.process()
    # tx.commit()

    return render_template('results.html',owner=owner, model=model)

if __name__ == "__main__":
    app.run()
