from collections.abc import MutableMapping
from elasticsearch import Elasticsearch 
import time 
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import requests
import re
import os
import yaml
from .INTERFACE import Interface


class Es(Interface):
    def __init__(self,nodes,auth:tuple = None):
        "If authentication is required, it must be given in a form of <id>:<password>"
        self.nodes = nodes
        self.agents = []
        for node in self.nodes:
            self.agents.append(re.sub(r"https",r"http",node).rsplit(":",maxsplit=1)[0] +":5000")
        if auth:
            self.auth = auth.split(":")    
    
    def connector(self) -> Elasticsearch:
        try :
            es= Elasticsearch(self.nodes,
                            sniff_on_node_failure=True,sniff_timeout=30,
                            basic_auth=(self.auth[0],self.auth[1] if hasattr(self, "auth") else None),
                            verify_certs=False #Same as "-k"
                            )
            return es
        except AttributeError as e:
            es= Elasticsearch(self.nodes,
                sniff_on_node_failure=True,sniff_timeout=30,
                verify_certs=False #Same as "-k"
                ) 
            return es
    
    # @staticmethod
    # def token_generator() -> str:
    #     serializer= Serializer("AGENT_KEY",300)
    #     return serializer.dumps({"confirm":True}).decode("utf-8")
    
    def RollingRestart(self):
        es_con = self.connector()
        for node in self.agents:
            while True : 
                try :
                    if es_con.cluster.health()['status'] =="green":
                        print("Cluster health green! Continue rolling restart...")
                        token = Es.token_generator()
                        res=requests.post(node+"/es/command/restart",json={"token":token})
                        if res.status_code == 200:
                            print(f"[SUCCESS] Agent : {node} executed Restart...")
                            time.sleep(10) 
                            es_con = self.connector() # recall 
                        else:
                            print(f"[ERROR] Agent : {node} restart failed...")
                except Exception as e:
                    print(f"[ERROR]! {e}")
                    print(e.args)
                    return False
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
    
    def ClusterHealthCheck(self) -> str:
        es_con = self.connector()
        try :
            return es_con.cluster.health().get("status")
        except Exception as e:
            return str(e)
    
    @property
    def Configuration(self) -> dict:
        #First, check the version of cluster
        es_con = self.connector()
        try : 
            version :str = es_con.info().get("version").get("number") 
            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, f'../solutions/elasticsearch/elasticsearch{version[0]}.yml')
            with open(filename,encoding='UTF8') as f:
                data = Es.flatten_dict(yaml.load(f,Loader=yaml.FullLoader))
                return data
                
        except Exception as e:
            print("error from exception")
            
            return e
    
    
    def SetConfiguration(self,dic:MutableMapping) -> bool:
        token = Es.token_generator()
        #Connect, and send this newly gotten dict
        error_reports=[]
        for node in self.agents:
            try:        
                res=requests.post(node+"/es/command/configuration",json={"token":token,"data":dic})
                if res.status_code == 200:
                    message= f"[SUCCESS] Agent '{node}' Set Config file..."
                    print("message")  
                else:
                    message = f"[ERROR] Sent a post request but agent '{node}' failed to set config file"
                    error_reports.append(message)
            except Exception as e:
                message =f"[Error] Post request to '{node}' failed !"
                print(message)
                error_reports.append(message)
        if not error_reports:
            return True,0
        else:
            return False,error_reports
    
    # flatenning dict--------
    @staticmethod
    def _flatten_dict_gen(d:dict,parent_key,sep):
        for k ,v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v,MutableMapping):
                yield from Es.flatten_dict(v,new_key,sep=sep).items()
            else:
                yield new_key,v
    
    @staticmethod
    def flatten_dict(d:MutableMapping, parent_key:str ="",sep:str="."):
        return dict(Es._flatten_dict_gen(d,parent_key,sep))
                


                        
                
