from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import os
import requests
import time


class Agent:
    AGENT_DIR=os.getenv("AGENT_DIR") 
    UNSYNC=0
    SYNC=1
    FAILURE=2
       
    def __new__(cls):
        return cls
    
    @staticmethod
    def token_generator() -> str:
        serializer= Serializer(os.getenv("AGENT_KEY"),300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    @staticmethod
    def _file_list():
        for _,file in zip(range(10000),os.listdir(Agent.AGENT_DIR)): #AGENT_DIR must be absolute path 
            if os.path.isfile(os.path.join(Agent.AGENT_DIR,file)): #file path as well
                yield str(_),open(os.path.join(Agent.AGENT_DIR,file),"rb") #Must be string or byte type
    
    @classmethod
    def file_load(cls):
        files={_:file for _,file in Agent._file_list()}
        cls.files=files
        cls.files["token"] = Agent.token_generator()
        
    @staticmethod
    def sync_status(node:str,timeout=3):
        try:
            res= requests.get(node+"/",timeout=timeout)
            if res.ok:
                if res.json().get("version") ==os.getenv("AGENT_VERSION"):
                    print("Version match")
                    return node,Agent.SYNC
                else:
                    print("Version not matched!")
                    return node,Agent.UNSYNC
        except requests.exceptions.ConnectionError as e:
            print("[ERROR] Connection to '{}' failed.".format(node))
            return node,Agent.FAILURE
    

    @staticmethod
    def agent_sync(node:str,files:dict):
        url = node + "/agent/command/sync"
        print(url)
        try:
            res=requests.post(url,files=files)
            if res.ok:
                print("[SUCCESS] Agent sync to {} completed successfully".format(node))
                return True
            else:
                print("[ERROR] Agent sync to {} failed".format(node))
                return False
        except requests.exceptions.ConnectionError as re:
            print("[ERROR] Connection to '{}' failed.".format(node))
            return False
        except Exception as e:
            print("[ERROR] {}".format(str(e)))
            return False

    @staticmethod
    def agent_restart(node:str):
        restart_url = node + "/agent/command/restart"
        try:
            restart_res=requests.post(restart_url,json={"token":Agent.token_generator()}) #Agent server will shut down briefly
        except requests.exceptions.ConnectionError as e: #we've already checked the connection
            print("Let's give a little sec '{}' failed.".format(node))
        except Exception as e:
            print("[ERROR] {}".format(str(e)))
            return False
        finally:
            cnt = 0 
            while cnt<10:
                try : 
                    res= Agent.sync_status(node)
                    if res[1] == 1:                   
                        print("[SUCCESS] Agent restart on {} completed successfully".format(node))
                        return True
                    else:
                        cnt+=1
                        time.sleep(0.5)
                        continue
                except requests.exceptions.ConnectionError as e:
                    print("[WORK_IN_PROGRESS] Agent is booting up again on {}, give more time...".format(node))
                    time.sleep(0.5)
                    cnt +=1
            else:
                print("[ERROR] Restart operation executed on {} but not rebooted!".format(node))
                return False

