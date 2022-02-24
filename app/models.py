from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


class User(UserMixin, db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(10),index=True)
    id = db.Column(db.Integer, primary_key=True)
    operations = db.relationship("Operation", backref="user",lazy="dynamic")
 
    email = db.Column(db.String(64),unique=True,index=True)
    password_hash = db.Column(db.String(128))

    #confirmed status
    confirmed = db.Column(db.Boolean, default=False)

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

    def generate_confirmation_token(self,expiration=300):
        s = Serializer(current_app.config["SECRET_KEY"],expiration)
        return s.dumps({"confirm":self.id}).decode("utf-8") #PK of this instance
    
    def confirm(self,token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True  #confirmed. Not confirm.
        db.session.add(self)
        return True


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

