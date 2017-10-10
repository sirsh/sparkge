import numpy as np
from . providers.stores import basic_store

store = basic_store()
   
class MappingException(Exception):  pass

class options(dict):   def __init__(self):pass
    
class sparkge_context:
    """
    Example
    arr = np.ones((100,20), np.int)
    def f (data) : return np.random.randint(0,100,len(data)) 
    sc =  sparkge_context() 
    res = sc.apply_function(arr, f)
    """
    def __init__(self, name = "sparkge_app", master="localhost"): 
        #putting imports here to only load if required
        import findspark
        findspark.init()
        import pyspark
        from pyspark.sql import SQLContext
        from pyspark import SparkConf, SparkContext
        from pyspark.sql import Row,SparkSession
 
        b = SparkSession.builder.appName(name).config("master", "spark://{}:7077".format(master))
        spark = b.getOrCreate()        
        self.sc = spark.sparkContext
        self.tracker = self.sc.statusTracker()
        self.sqlContext = SQLContext(self.sc)  
        def finalise():SparkSession._instantiatedContext = None 
            
        self.finalize = finalise 
        
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback): 
        if self.sc != None: 
            self.sc.cancelAllJobs()
            self.sc.stop()
            self.sc = None
            self.finalize()
            
    def _partition_population(self, pop, batchsize=10):
        from itertools import islice, chain

        index = list(range(len(pop)))
        def batch(iterable, size=batchsize):
            sourceiter = iter(iterable)
            while True:
                batchiter = islice(sourceiter, size)
                yield chain([next(batchiter)], batchiter)
        
        for _batch in batch(range(len(pop))):
            index = list(_batch)
            yield {"index": index,  "data" : pop[index] }
    
    def _recover_population_from_parititions(self, parts):
        return np.concatenate(parts)
        
    def apply_function(self, gen, _f, collect=True, batching=True):
        f = _f
        if batching: 
            gen = self._partition_population(gen)
            f= lambda tup :  _f(tup["data"]) #np.stack([np.array(tup["index"]), _f(tup["data"])],axis=1) #for bookkeeping we can check the index TODO -the order is very important!!!
        if self.sc != None:
            if not collect:  return self.sc.parallelize(gen).map(lambda x: f(x)).count()
            else:  
                res = self.sc.parallelize(gen).map(lambda x: f(x)).collect()
                return res if not batching else self._recover_population_from_parititions(res)
        else: print("***********skipping jobs due to failed context loading*************")
    
def __deploy__(target_list):
    from fabric.api import execute, parallel, run
    from fabric.state import output
    command = "pip3 install git+git://github.com/sirsh/sparkge --upgrade"
    @parallel
    def p(): return run(command)
    print("deploying to ", target_list)
    res = execute(p, hosts=target_list)
    for k in res.keys():
        print("**********", k, "done ************")
        for l in res[k].splitlines():
            print(l)
            