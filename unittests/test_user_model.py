import unittest
from app.models import User,AnonymousUser,Permission,Role
from app import create_app,db
import time 

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        #You have to assign roles
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password = "dog")
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password = "cat")
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password="cat")
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))
        
    def test_password_salts_are_random(self):
        u1 = User(password="cat")
        u2 = User(password="cat")
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password="cat")
        u2 = User(password="dog")
        db.session.add_all([u1,u2])
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='tiger')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_user_role(self):
        u = User(email ="john@wemakeprice.com", password="cat") #assign default role
        #self.assertTrue(u.can(Permission.READ))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.EXECUTE))
        self.assertFalse(u.can(Permission.ADMIN))
    
    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.READ))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.EXECUTE))
        self.assertFalse(u.can(Permission.ADMIN))
    def test_admin_role(self):
        u = User(email ="migo@wemakeprice.com", password="cat") 
        self.assertTrue(u.can(Permission.READ))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.EXECUTE))
        self.assertTrue(u.can(Permission.ADMIN))