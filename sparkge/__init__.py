from . import symbols
from . import evolution 
    
class MappingException(Exception):  pass

class options(dict):
    def __init__(self):pass
    
class context:
    def __init__(self,store_provider,start_symbol,options=None):
        self.store = store_provider
        self.options = options
        self.start_symbol = start_symbol
        self.sc = None# setup spark context in this context
    
    def __init__(self):
       
        pass
    def __enter__(self):
        self.store.broadcast()
    def __exit__(self):
        self.store.report()        
    def __iter__(self):
        return iter(store) 
    def __getitem__(self,key):
        return store[key]  
    
    @property
    def keys(self):
        pass
 
    def transcribe(self, genome, params = []):
        phenotype = self.start_symbol(genome,params)
        return accepting_ordered_params(phenotype,params)#think about who controls the param order
    
    def evolve(self,options):
        genotypes = self.store.genotypes
        pool_index,replacement_index = evo.selection(self.store.meta_individuals)
        genotypes = np.concatenate([genotypes[replacement_index], 
                                    X(genotypes[pool_index])]) + evo.mutations(0.01)
        self.store.update(genotypes)
        
    def run(self,eval_func):
        #store.update(evolution.init())
        #transcribe returns function of a matrix and eval_func_prov takes such a thing
        worker_func = lambda key: eval_func(self.transcribe(self.cache[key]))
        for gen in self.options.generations:  
            results = self.sc.map(self.keys).reduce(lambda key: worker_func(key)).collect() #results should be id,score
            self.store.update(results)
            self.evolve()
            