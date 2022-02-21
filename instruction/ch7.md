## Large Application Structure

The way to structure the application in Flask is left entirely to developer.<br>
So here, the possible way to organize a large application is presented.<br>

Basic Layout:<br>
|-project<br>
    |-app<br>
        |-templates/<br>
        |-static/<br>
        |-main/<br>
            |-\_\_init\_\_.py<br>
            |-errors.py<br>
            |-forms.py<br>
            |.views.py<br>
        |-\_\_init\_\_.py<br>
        |-email.py<br>
        |-models.py<br>
    |-migrations/<br>
    |-tests/<br>
        |-\_\_init\_\_.py<br>
        |-test*.py<br>
    |-venv/<br>
    |-requirements.txt<br>
    |-config.py<br>
    |-project_name.py<br>
<br>
