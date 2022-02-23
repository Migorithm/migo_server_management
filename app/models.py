from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from . import login_manager

class User(UserMixin, db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(10),index=True)
    id = db.Column(db.Integer, primary_key=True)
    operations = db.relationship("Operation", backref="user",lazy="dynamic")
 
    email = db.Column(db.String(64),unique=True,index=True)
    def __repr__(self):
        return "<User %r>" % self.username
    
    @property
    def password(self):
        raise AttributeError("Not Readable Attribute")
    
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)


class Operation(db.Model):
    __tablename__ = "operations"
    id = db.Column(db.Integer,primary_key=True)
    operation = db.Column(db.String(64),nullable=False,index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    def __repr__(self):
        return "<Operation %r>" % self.operation
    
# To load "a" user, we need to define
# User loading function 
@login_manager.user_loader 
def load_user(user_id):
    return User.query.get(int(user_id))

