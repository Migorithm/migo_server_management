from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
from typing import Generator
import requests

class Agent:
    AGENT_DIR=os.getenv("AGENT_DIR") 
       
    def __new__(cls):
        return cls
    
    @staticmethod
    def token_generator() -> str:
        serializer= Serializer("AGENT_KEY",300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    @staticmethod
    def _file_list()-> Generator[tuple]:
        for _,file in zip(range(10000),os.listdir(Agent.AGENT_DIR)):
            if os.path.isfile(file):
                yield str(_),open(file,"rb") #Must be string or byte type
    
    @classmethod
    def file_load(cls):
        files={_:file for _,file in Agent._file_list()}
        cls.files=files
        cls.files["token"] = Agent.token_generator()
        
    @staticmethod
    def status(node:str):
        res= requests.get(node+"/")
        if res.ok:
            if res.json().get("version") ==os.getenv("AGENT_VERSION"):
                print("Version match")
                return True
            else:
                return False
        else:
            raise ConnectionError("Connection to '{}' failed.".format(node))
    
    @staticmethod
    def agent_sync(nodes:list[str],files:dict):
        success=[]
        for node in nodes:
            url = node + "/file_upload"
            res=requests.post(url,files=files)
            if res.ok:
                print("Agent sync to {} completed successfully".format(node))
                success.append(True)
            else:
                print("Agent sync to {} went wrong".format(node))
                success.append(False)
        if all(success):
            return True
        else:
            return False
