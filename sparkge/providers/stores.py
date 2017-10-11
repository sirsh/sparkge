"""
Stores are an abstraction to dump data and save/log/report etc.

"""
class aerospike_store:
    def __init__(self,options=None):
        pass
    
    def update(self,meta, genes):
        pass
    
    def broadcast(self):
        pass
    
    def report(self):
        pass
    
    def lazy_query(self,qry_str):
        def _query():
            pass
        return _query
    
    
class basic_store:
    def __init__(self,options=None):
        pass
    
    def update(self,meta, genes):
        pass
    
    def broadcast(self):
        pass
    
    def report(self):
        pass
    
    def lazy_query(self,qry_str):
        def _query():
            pass
        return _query
    