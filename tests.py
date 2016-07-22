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

        graph = Graph(os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474'),bolt=False)
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
