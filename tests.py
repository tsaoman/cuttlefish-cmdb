
#=========#
# MODULES #
#=========#

import os
import app
import unittest
import tempfile
import sys
from py2neo import Graph

#====================#
# MAIN TESTING CLASS #
#====================#

class AppTestCase(unittest.TestCase):

    #setup
    def setUp(self):
        self.app = app.app.test_client()

        graph = Graph(password="origami abase squander costive")
        graph.run("MATCH (a) DETACH DELETE a") #clears graph

    def testPOSTandDBUpdate(self):
        rv = self.app.post('/tx', data=dict(owner="Testivus",model="Skynet"),follow_redirects=True)
        unittest.TestCase.assertEqual(self,rv.status_code,200)

        rv = self.app.get('/api/return/person/Testivus')
        unittest.TestCase.assertIn(self,'Testivus',rv.get_data(as_text=True))

        rv = self.app.get('/api/return/asset/Skynet')
        unittest.TestCase.assertIn(self,'Skynet',rv.get_data(as_text=True))

#test runner
suite = unittest.TestLoader().loadTestsFromTestCase(AppTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)
