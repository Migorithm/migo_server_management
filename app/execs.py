######################################################################
# Builder pattern to insert executables into each solution
#
#
######################################################################

from abc import ABC,abstractmethod

class IExecutableBuilder(ABC):
    "The Executable Builder interface"
    
    @staticmethod
    @abstractmethod
    def set_solution_type(solution:str):
        "Solution name"
        
    @staticmethod
    @abstractmethod
    def set_executable(executable:str):
        "Set executable"
        
class ExecutableBuilder(IExecutableBuilder):
    "The Executable Builder"
    def __init__(self):
        self.execution=[]
    
    def set_solution_type(self,solution:str):
        self.solution = solution
        return self
    
    def set_executable(self,executable:str):
        self.execution.append(executable)
        return self
    
    def get_result(self):
        res = self.Execution(self).__dict__
        return {"solution":self.solution,"execution":[key for key in res]}
        
    class Execution:
        def __init__(self,builder_instance):
            for order,exe in enumerate(builder_instance.execution,1):
                setattr(self,exe,order)
    
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
    

class RedisDirector:
    "Redis Director that can build a complex representation."
    @staticmethod
    def construct():
        """Constrcut and return the final product."""
        return ExecutableBuilder()\
            .set_solution_type("Redis")\
            .set_executable("RollingRestart")\
            .set_executable("FileTransfer")\
            .set_executable("Ping")\
            .get_result()
