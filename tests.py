import os
import app
import unittest
import tempfile

class AppTestCase(unittest.TestCase):

    #setup
    def setUp(self):
        self.app = app.app.test_client()

    def testPostandAssetAdd(self):
        rv = self.app.post('/tx', data=dict(owner="Testivus",model="Skynet"),follow_redirects=True)
        unittest.TestCase.assertEqual(self,str(rv),'<Response streamed [200 OK]>','POST Failed')

    # def testDBPersistence(self):
    #     rv = self.app.get('/api/results/Testuvus')
    #     print (rv)

suite = unittest.TestLoader().loadTestsFromTestCase(AppTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)
