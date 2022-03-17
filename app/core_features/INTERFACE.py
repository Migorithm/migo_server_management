from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from abc import ABC,abstractmethod
class Interface(ABC):
    "Interface for solution you use"
    
    @staticmethod
    def connector():
        "In case of using connector module; method for connection to solutions"
        
    
    @staticmethod
    def token_generator() -> str:
        serializer= Serializer("AGENT_KEY",300)
        return serializer.dumps({"confirm":True}).decode("utf-8")
    
    @staticmethod
    @abstractmethod
    def RollingRestart():
        "abstract method for rolling restart"
        
    @staticmethod
    @abstractmethod
    def ClusterHealthCheck():
        "abstract method for cluster health check"
    
    @staticmethod
    @abstractmethod
    def Configuration():
        "abstract method for getting configuration info"

    @staticmethod
    @abstractmethod
    def SetConfiguration():
        "abstract method for configuration modification"
    