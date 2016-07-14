import os
import app
import unittest
import tempfile

class AppTestCase(unittest.TestCase):

    #setup
    def setUp(self):
        self.app = app.app.test_client()

    def testPOSTandDBUpdate(self):
        rv = self.app.post('/tx', data=dict(owner="Testivus",model="Skynet"),follow_redirects=True)
        unittest.TestCase.assertEqual(self,str(rv),'<Response streamed [200 OK]>','POST Failed')

    def testGET(self):
        rv = self.app.get('/api/return/person/Testivus')
        unittest.TestCase.assertEqual(self,str(rv),'<Response streamed [200 OK]>','GET Failed')

        rv = self.app.get('/api/return/asset/Skynet')
        unittest.TestCase.assertEqual(self,str(rv),'<Response streamed [200 OK]>','GET Failed')

    # def testDBPersistence(self):
    #     rv = self.app.get('/api/return/person/Testivus')
    #     print ('\n',type(rv))





#test runner
suite = unittest.TestLoader().loadTestsFromTestCase(AppTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)
