from collections.abc import MutableMapping
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import requests
import time 
from .INTERFACE import Interface

class Redis(Interface):
    def __init__(self,nodes,auth=None):
        self.nodes=nodes
        self.auth = auth
        self.agents=[]
        for node in self.nodes: #10.107.11.66:6379
            agent = node.split(":")
            self.agents.append((agent[0],int(agent[1])))

    def ClusterHealthCheck(self):
        import socket
        success=[]
        for node in self.agents:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(node) #tuple type
                    sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                    if self.auth:
                        sock.sendall(f"auth {self.auth}\r\n".encode())
                        sock.recv(1024)
                    sock.sendall(b"ping\r\n")
                    if sock.recv(1024) == b"+PONG\r\n":
                        success.append(True)
                    else:
                        #print(f"[ERROR] Connection to {node} failed!")
                        success.append(False)
                except Exception as e:
                    #print(f"[ERROR] Connection to {node} failed!")
                    success.append(False)
        if all(success):
            return True
        else:
            return False
                    
    @staticmethod
    def token_loader(token):
        serializer = Serializer()
        return serializer.loads(token.encode("utf-8"))
    
    def RollingRestart(self):
        for node in self.agents:
            while True:
                try :
                    if self.ClusterHealthCheck():
                        print("Cluster health green! Continue rolling restart...")
                        token = Redis.token_generator()
                        res = requests.post("http://"+node[0]+":5000/redis/command/restart",json={"token":token,"port":node[1]})
                        if res.status_code==200:
                            print(f"[SUCCESS] Agent : {node} executed Restart...")
                            time.sleep(10) 
                        else:
                            print(f"[ERROR] Agent : {node} restart failed...")
                    else:
                        raise Exception(f"Connection to {node} failed!")
                except Exception as e:
                    print(f"[ERROR] {e}")
                    return False
                else:
                    cnt =0
                    MAXTRIAL = 5
                    while not self.ClusterHealthCheck() and cnt <MAXTRIAL:
                        print("Cluster health not green! give it a little sec")
                        time.sleep(5)
                        cnt+=1
                        print(f"Tried {cnt} times...")
                        print(f"The most recent execution was on {node}")
                        continue
                    if not cnt<MAXTRIAL:
                        return False
                    else:
                        break  
        return True
                    
    @property
    def Configuration(self):
        #Fetch current data from the first server. 
        file:dict
        error:Exception 
        for node in self.agents:
            try: 
                token = Redis.token_generator()
                print(node)
                res = requests.post("http://"+node[0]+":5000/redis/command/get_config",json={"token":token,"port":node[1]})
                #You will get the json form of data
                file = res.json()
                return file
            except Exception as e:
                error=e
        return error
        #process it
        
        
    def SetConfiguration(self,dic:MutableMapping) -> bool:
        token = Redis.token_generator()
        error_reports=[]
        for node in self.agents:
            try:
                res = requests.post("http://"+node[0]+":5000/redis/command/set_config",json={"token":token,"data":dic,"port":node[1]})
                if res.status_code == 200:
                    message =f"[SUCCESS] Agent '{node}' Set Config file..."
                    print(message)
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