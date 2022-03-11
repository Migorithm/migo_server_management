from elasticsearch import Elasticsearch 
import time 
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import requests
import re

class EsRollingRestart:
    def __init__(self,nodes,auth:tuple = None):
        "If authentication is required, it must be given in a form of <id>:<password>"
        self.nodes = nodes
        self.agents = []
        for node in self.nodes:
            self.agents.append(re.sub(r"https",r"http",node).rsplit(":",maxsplit=1)[0] +":5000")
        if auth:
            self.auth = auth.split(":")    
    
    def connector(self) -> Elasticsearch:
        es= Elasticsearch(self.nodes,
                        sniff_on_node_failure=True,sniff_timeout=30,
                        http_auth=(self.auth[0],self.auth[1]) if self.auth else None,
                        verify_certs=False #Same as "-k"
                        )
        return es
    
    @staticmethod
    def token_generator() -> str:
        serializer= Serializer("AGENT_KEY",300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    def RollingRestart(self):
        es_con = self.connector()
        for node in self.agents:
            while True : 
                try :
                    if es_con.cluster.health()['status'] =="green":
                        print("Cluster health green! Continue rolling restart...")
                        print("execute 1") #to be replaced with post request
                        token = EsRollingRestart.token_generator()
                        print(token)
                        res=requests.post(node+"/command/restart",json={"token":token})
                        if res.status_code == 200:
                            print(f"Agent : {node} executed Restart...")
                            time.sleep(10) 
                except Exception as e:
                    print(f"Error occured! {e}")
                    print(e.args)
                else:
                    cnt=1
                    #Proceeding with rolling restart with cluster health being yellow or red is banned. 
                    while es_con.cluster.health()['status'] != "green":
                        print("Cluster health not green! give it a little sec")
                        print(f"Tried {cnt} times...")
                        print(f"The most recent execution was on {node}")
                        time.sleep(10)
                        cnt+=1
                        continue
                    else:
                        break
        else:
            return True
            
            
