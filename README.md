# Cuttlefish CMDB
Configuration Management Database leveraging Neo4j (graph database). Represents networks as they exist in real life (as a graph).

This project is still in development. The majority of it is untested. I would also avoid storing sensitive data until auth is added.

## Usage

### Local Deployment

Initialize a Neo4j DB instance on port 7474 (default).
Navigate to project directory and run `gunicorn app:app`.
It should run on port 8000.

### Heroku

This application is available on [Heroku](https://cuttlefish-cmdb.herokuapp.com/).
As auth is not yet enabled, everyone shares the same database.
As such, I don't see how this can be useful for its intended purposes.
But it's here nonetheless.

## Current functionality

As of now, Cuttlefish is just a fancy datastore. You can add an asset and its owner, and see it displayed in the asset list. You can change properties off assets (except owner). You can also remove assets. These are stored in a Neo4j database. So basically, this doesn't do anything you can't already do with Neo4j and Cypher. Unless of course you don't know Cypher. But it's a lot prettier here. 

##TBD

Major updates, loosely ordered by priority, include
- graph visualization of networks
- automatically adding assets via a network scan or uploading of network logs
- Adding users via some directory API is also on my list.

Small changes, loosely ordered by priority, include
- bootstrap / datatables: CDN to local

## Testing

Warning: Testing will clear the local Neo4j database. Do not test if you have important data loaded. Not that end users should be testing things anyway.

## Licence / Copyright

This project is licensed under GNU AGPLv3. It can be found LICENSE.txt.

## Contact

Author: Brandon Tsao.  
Email: BrandonSTsao@gmail.com
