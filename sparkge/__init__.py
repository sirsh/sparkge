from . providers.stores import basic_store

store = basic_store()
   
class MappingException(Exception):  pass

class options(dict):
    def __init__(self):pass
    
class sparkge_context:
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
            f= lambda tup : np.stack([np.array(tup["index"]), _f(tup["data"])],axis=1)
        if self.sc != None:
            if not collect:  return self.sc.parallelize(gen).map(lambda x: f(x)).count()
            else:  
                res = self.sc.parallelize(gen).map(lambda x: f(x)).collect()
                return res if not batching else self._recover_population_from_parititions(res)
        else: print("***********skipping jobs due to failed context loading*************")
    
