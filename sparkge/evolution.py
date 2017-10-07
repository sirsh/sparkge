import random
import numpy as np
import pandas as pd
from . import MappingException

CODON_MAX  = 100
MIN_L, MAX_L, N = 10,10**2,10**3
MRATE = 0.01
SRATE = 0.7

lpad = lambda v,n : np.pad(v.astype(float), (n-len(v),0), 'constant', constant_values=np.NAN)
rpad = lambda v,n : np.pad(v.astype(float), (0,n-len(v)), 'constant', constant_values=np.NAN)
random_individual = lambda l : np.random.randint(0,CODON_MAX, size=l)
random_padded_individual = lambda l,L : rpad(random_individual(l),L)
generate_from_lengths = lambda ls : np.stack( [random_padded_individual(l,MAX_L) for l in ls])
cut_matrix = lambda n :np.stack( [rpad(np.ones(l),MAX_L) for l in np.random.randint(0,MAX_L,size=n)])
lengths = lambda p : np.sum(~np.isnan(p),axis=1)

class strategy:
    def __init__(self, pop_size, genome_size, srate, mrate):
         pass
        
    def init():
        individual_lengths = np.random.randint(MIN_L, MAX_L, size=N)
        individual_fitnesses = np.full(N,np.nan)
        individual_genotypes = generate_from_lengths(individual_lengths)
        return individual_lengths, individual_fitnesses, individual_genotypes

    def _x(a,b):
        c = np.concatenate([a,b],axis=1)
        def f(row):
            r = row[~np.isnan(row)]
            return rpad(r, MAX_L) if len(r) < MAX_L else r[:MAX_L]
        return np.apply_along_axis(f, 1, c)

    def X(pool):
        chromosomes = pool * cut_matrix(len(pool))
        split = int(len(pool) / 2) # it should be known that this is div by 2
        return np.concatenate([_x(chromosomes[split:], chromosomes[:split]),
                              _x(chromosomes[:split], chromosomes[split:])])

    def selection(individuals):
        K = int(SRATE*N) 
        mates = 2*int(N-K)
        replacement = N-mates
        scores = individuals[:,1] #1 is the index of scores on the ind matrix
        scores = scores - scores.max() #minimise
        scores = scores / scores.sum() #normalize
        selected = np.random.choice(range(N),mates+replacement,p=scores) 
        return selected[:mates], selected[mates:]

    def mutations(rate):
        mar = np.full(N*MAX_L,np.nan)
        idx = np.random.randint(N*MAX_L, size=int(N*MAX_L*MRATE))
        mar[idx]= np.random.randint(CODON_MAX, size=len(idx))
        return mar.reshape((N,MAX_L))

class chain:
    def __init__(self,l=None, max_wraps=3, default_length=30): 
        if l is None: l = np.random.randint(0,10,default_length)
        l = np.concatenate([l for i in range(max_wraps)])
        self._l, self.length = l,len(l)
        self._index = 0
     
    def __getitem__(self, key):
        if key >= self.length: return None
        return self._l[ key ]
    
    def _next(self): 
        if self._l is None: return random.randint(0,10)
        if self._index < self.length: 
            self._index += 1
            return self[self._index-1]
        return None
        
    def choose(self, choices):
        cn = self._next()
        if cn ==None: raise MappingException("we ran out of codons")
        return choices[cn % len(choices)] if len(choices) > 1 else choices[0]
    
def expr(genome=None, args = []):
    f = genome.choose([op(expr,expr), var])
    try: 
        expressed = f(genome,args)
        def _f(**kwargs): return expressed(**kwargs)
        return _f
    except MappingException as mex: 
        def _f(**kwargs): return np.nan
        return _f