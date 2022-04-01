### Configuration & Environment variable
You should put any credentials and sensitive infomration into environment variable.<br>
In this project, I used ".flaskenv" for it.<br><br>

Information that should be kept under wrap is:
- "AUTH_" for authentication of ES cluster id and password
- "SECRET_KEY" for flaskform and JWT
- "AGENT_KEY" for master-agent confirmation
- "ADMINS" to register admin mail
- "DOMAIN" to block any other users who has no specified domain in their email from registration
- "MAIL_SERVER" for SMTP
- "SOLUTION" to specify managed solution and its constituent clusters and nodes

<br><br>


#### app.execs.py
With builder pattern applied, this is where you define available execution for each solution. Take ElasticSearch for example:
```python
class ElasticDirector:
    "Elastic Director that can build a complex representation."
    @staticmethod
    def construct():
        """Constrcut and return the final product."""
        return ExecutableBuilder()\
            .set_solution_type("ElasticSearch")\
            .set_executable("RollingRestart")\
            .set_executable("FileTransfer")\
            .set_executable("ClusterHealthCheck")\
            .get_result()
```
If you want to add more functionality, you can simply modify the return part by setting **".set_executable("command you want")"**
<br>

And then, you can have the feature registered to ***Execution*** model: 
```python
class Execution(db.Model):
    ...
    ...

    @staticmethod
    def insert_execution():
        REDIS= RedisDirector.construct() #dict - solution, execution
        ELASTIC = ElasticDirector.construct() #dict 
        SOLUTIONS=[REDIS,ELASTIC]
        for sol in SOLUTIONS:
            for exe in sol["execution"]:
                execution = Execution.query.filter_by(name=exe,solution=sol["solution"]).first()
                if execution is None:
                    execution = Execution(name=exe,solution=sol["solution"])
                db.session.add(execution)
            db.session.commit()
```
<br>

As you can imagine, you can simply get into flask shell and execute the following:
*flask shell*:
```python
a= Execution()
a.insert_execution()
```

#### Adding User role 
```python
role = Role()
role.insert_roles()
```

#### Authentication 
.flaskenv
```
AUTH_Cluster_name=Password
```



## Installation Procedure
On terminal
1. flask db init
2. flask db migrate
3. flask db upgrade
4. flask shell

```python
a = Execution()
a.insert_execution()

role = Role()
role.insert_roles()
```