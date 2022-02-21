## Large Application Structure

The way to structure the application in Flask is left entirely to developer.<br>
So here, the possible way to organize a large application is presented.<br>

Basic Layout:<br>
|-project
    |-app
        |-templates/
        |-static/
        |-main/
            |-\_\_init\_\_.py
            |-errors.py
            |-forms.py
            |.views.py
        |-\_\_init\_\_.py
        |-email.py
        |-models.py
    |-migrations/
    |-tests/
        |-\_\_init\_\_.py
        |-test*.py
    |-venv/
    |-requirements.txt
    |-config.py
    |-project_name.py
