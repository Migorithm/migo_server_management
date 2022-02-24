from datetime import timedelta
from flask import Flask
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager=LoginManager()
login_manager.login_view="auth.login" #sets the endpoint for login page
login_manager.remember_cookie_duration = timedelta(minutes=30) #session management

#Factory
def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(config[config_name])

    #staticmethod init_app
    config[config_name].init_app(app)
    

    #initialization of extensions.
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    #Blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')

    return app
