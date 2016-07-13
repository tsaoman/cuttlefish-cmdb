import os
import app
import unittest
import tempfile

class AppTestCase(unittest.TestCase):

    #setup
    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

        #don't know if necessary...
        # with app.app.app_context():
        #     app.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.app.config['DATABASE'])

    #=======#
    # TESTS #
    #=======#

    def tx(self,owner,model):
        self.app.post('/tx',data=dict(owner=owner,model=model),follow_redirects=True)

    def test_tx(self):
        rv = self.tx('Joy','MacBookAir')



# if __name__ == '__main__':
#     unittest.main()
suite = unittest.TestLoader().loadTestsFromTestCase(AppTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)
