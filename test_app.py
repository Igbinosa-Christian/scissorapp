import unittest
from app import application, db, User, Link, VisitLocation
from flask_login import LoginManager,login_user,logout_user,login_required,current_user,UserMixin

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = application.test_client()
        self.app_context = application.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        

    def test_register_route(self):
        response = self.app.post('/register', data=dict(
            username='testuser',
            email='test@example.com',
            password='password',
            con_password='password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        

    def test_login_route(self):
        user = User(username='testuser', email='test@example.com', password_hash='password')
        db.session.add(user)
        db.session.commit()
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='password'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)


    def test_logout_route(self):
        response = self.app.get('/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        

if __name__ == '__main__':
    unittest.main()
