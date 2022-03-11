import os
from app import create_app,db
from app.models import User,Operation,Role,AnonymousUser,Execution
from flask_migrate import Migrate
import click

app = create_app(os.getenv("FLASK_CONFIG") or 'default')

#To expose flask db + subcommand.
migrate = Migrate(app,db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db,User=User,Operation=Operation,Role=Role,AnonymousUser=AnonymousUser,Execution=Execution)


@app.cli.command()
def unittest(test_names=None):
    """ Run the unit tests"""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover("unittests")
    unittest.TextTestRunner(verbosity=2).run(tests)
