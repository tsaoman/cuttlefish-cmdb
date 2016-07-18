# Cuttlefish CMDB
Configuration Management Database leveraging Neo4j (graph database). Represents networks as they exist in real life.

This project is still in its fetal stage. The majority of it is untested. I would also avoid storing sensitive data until auth is added.

## Current functionality

You can add an asset and its owner, and see it displayed in the asset list. These are stored in a Neo4j database. So basically, this doesn't do anything you can't already do with Neo4j and Cypher. Unless of course you don't know Cypher.

##TBD

Loosely ordered by priority

- Add more asset / person attributes
- Allow editing asset / owner information
- bootstrap / datatables: CDN to local
- Upload / scan features - allow for uploading of logs or scanning of network

## Testing

Warning: Testing will clear the local Neo4j database. Do not test if you have important data loaded. Not that users should be testing things anyway.

## Licence / Copyright

This project is licensed under GNU AGPLv3. It can be found LICENSE.txt.

## Contact

Author: Brandon Tsao.
Email: BrandonSTsao@gmail.com
