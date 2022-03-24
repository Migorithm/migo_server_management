from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
import requests

class Agent:
    AGENT_DIR=os.getenv("AGENT_DIR") 
    UNSYNC=0
    SYNC=1
    FAILURE=2
       
    def __new__(cls):
        return cls
    
    @staticmethod
    def token_generator() -> str:
        serializer= Serializer("AGENT_KEY",300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    @staticmethod
    def _file_list():
        for _,file in zip(range(10000),os.listdir(Agent.AGENT_DIR)): #AGENT_DIR must be absolute path 
            if os.path.isfile(file):
                yield str(_),open(file,"rb") #Must be string or byte type
    
    @classmethod
    def file_load(cls):
        files={_:file for _,file in Agent._file_list()}
        cls.files=files
        cls.files["token"] = Agent.token_generator()
        
    @staticmethod
    def sync_status(node:str):
        try:
            res= requests.get(node+"/")
            if res.ok:
                if res.json().get("version") ==os.getenv("AGENT_VERSION"):
                    print("Version match")
                    return Agent.SYNC
                else:
                    print("Version not matched!")
                    return Agent.UNSYNC
        except requests.exceptions.ConnectionError as e:
            print("Connection to '{}' failed.".format(node))
            return Agent.FAILURE
    
    @staticmethod
    def agent_sync(nodes:list[str],files:dict):
        success=[]
        for node in nodes:
            url = node + "/agent/command/sync"
            
            res=requests.post(url,files=files)
            if res.ok:
                print("[SUCCESS] Agent sync to {} completed successfully".format(node))
                success.append(True)
            else:
                print("[ERROR] Agent sync to {} failed".format(node))
                success.append(False)
        return all(success)

    @staticmethod
    def agent_restart(nodes:list[str]):
        success=[]
        for node in nodes:
            url = node + "/agent/command/restart"
            res=requests.post(url,json={"token":Agent.token_generator()})
            if res.ok:
                print("[SUCCESS] Agent restart on {} completed successfully".format(node))
                success.append(True)
            else:
                print("[ERROR] Agent restart on {} failed".format(node))
                success.append(False)
        return all(success)