from collections.abc import MutableMapping
import time 
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import requests
import re
import os
import yaml
from .INTERFACE import Interface
import socket
import ssl
import base64
import json
import random

class Es(Interface):
    def __init__(self,nodes,auth:tuple = None):
        "If authentication is required, it must be given in a form of <id>:<password>"
        self.nodes :list[str]= nodes
        self.auth = auth
        if self.nodes[0].startswith=="https":
            self.https=True
        else:
            self.https=False
        self.agents = []
        
        for idx in range(len(self.nodes)):
            self.agents.append(re.sub(r"https",r"http",self.nodes[idx]).rsplit(":",maxsplit=1)[0] +":5000")
            ip,port = re.search(r"[0-9]{2,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}:[0-9]{4}",self.nodes[idx]).group().split(":")# (123.123.23.24,9200)
            self.nodes[idx] = (ip,int(port))
            

    def es_con(self,path='/_cluster/health',get="status") -> str:
        node = random.choice(self.nodes)
        
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            if self.https:
                sock = ssl.wrap_socket(sock,keyfile=None,certfile=None,server_side=False,cert_reqs=ssl.CERT_NONE,ssl_version=ssl.PROTOCOL_SSLv23)
            sock.settimeout(3)
            try :
                sock.connect(node)
            except TimeoutError as t:
                self.es_con(path=path,get=get)
            except Exception as e:
                return str(e)

            else:
            #HTTP communication protocol
                path = path
                host = node[0]
                if self.auth :
                    token = base64.b64encode(self.auth.encode("ascii"))
                    lines = [
                    'GET %s HTTP/1.1' % path,
                    'Host: %s' % host,
                    'Authorization: Basic %s' %token.decode()
                    ]
                else :
                    lines = [
                    'GET %s HTTP/1.1' % path,
                    'Host: %s' % host,
                    ]

                #sock.send
                sock.send(("\r\n".join(lines) +"\r\n\r\n").encode())
                response=sock.recv(4096).decode()
                separator=response.index("{")
                result = json.loads(response[separator:])
                return result.get(get)

    

    @staticmethod
    def token_generator() -> str:
        serializer= Serializer(os.getenv("AGENT_KEY"),300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    def RollingRestart(self):
        #es_con = self.connector()
        for ip,port in self.nodes: # ip:str,port:int 
            while True : 
                try :
                    # if es_con.cluster.health()['status'] =="green":
                    if self.es_con() == "green":
                        print("Cluster health green! Continue rolling restart...")
                        token = Es.token_generator()
                        
                        res=requests.post("http://"+ip+":5000/es/command/restart",json={"token":token,"port":str(port)})
                        if res.status_code == 200:
                            print(f"[SUCCESS] Agent : {ip} executed Restart...")
                            time.sleep(10) 
                            #es_con = self.connector() # recall 
                        else:
                            print(f"[ERROR] Agent : {ip} restart failed...")
                except Exception as e:
                    print(f"[ERROR]! {e}")
                    print(e.args)
                    return False
                else:
                    cnt=1
                    #Proceeding with rolling restart with cluster health being yellow or red is banned. 
                    while self.es_con() != "green":
                        print("Cluster health not green! give it a little sec")
                        print(f"Tried {cnt} times...")
                        print(f"The most recent execution was on {ip}")
                        time.sleep(10)
                        cnt+=1
                        continue
                    else:
                        break
        else:
            return True
    
    def ClusterHealthCheck(self) -> str:
        try :
            return self.es_con()
        except Exception as e:
            return str(e)
    
    @property
    def Configuration(self) -> dict:
        #First, check the version of cluster
        #es_con = self.connector()
        try : 
            # version :str = es_con.info().get("version").get("number") 
            version :str = self.es_con(path='/',get="version").get("number")
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
        for ip,port in self.nodes:
            try:        
                print(token)
                res=requests.post("http://"+ip+":5000/es/command/configuration",json={"token":token,"data":dic,"port":str(port)})
                if res.status_code == 200:
                    message= f"[SUCCESS] Agent '{ip}' Set Config file..."
                    print(message)  
                else:
                    message = f"[ERROR] Sent a post request but agent '{ip}' failed to set config file"
                    error_reports.append(message)
            except Exception as e:
                message =f"[Error] Post request to '{ip}' failed !"
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
                


                        
                
