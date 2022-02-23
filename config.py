import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY= os.getenv("SECRET_KEY")

    #Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SUBJECT_PREFIX = '[Vertica]'
    MAIL_SENDER = 'Vertica Admin <noreply@example.com>'
    ADMINS=json.loads(os.getenv("ADMINS"))

    #DB
    SQLALCHEMY_TRACK_MODIFICATIONS=False 

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI=os.environ.get("DEV_DATABASE_URL") or\
        "sqlite:///" +os.path.join(basedir,"data-dev.sqlite")
    
class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI=os.environ.get("TEST_DATABASE_URL") or\
        "sqlite://"
    #In memory

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL") or\
        "sqlite:///" +os.path.join(basedir,"data.sqlite")


config = {
    "dev" : DevelopmentConfig,
    "test" : TestingConfig,
    "prod" : ProductionConfig,
    "default" : DevelopmentConfig
}