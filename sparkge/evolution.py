import random
import numpy as np
import pandas as pd
from . import MappingException

CODON_MAX  = 100
MIN_L = 10
lpad = lambda v,n : np.pad(v.astype(float), (n-len(v),0), 'constant', constant_values=np.NAN)
rpad = lambda v,n : np.pad(v.astype(float), (0,n-len(v)), 'constant', constant_values=np.NAN)
random_individual = lambda l : np.random.randint(0,CODON_MAX, size=l)
random_padded_individual = lambda l,L : rpad(random_individual(l),L)
length_of = lambda p : np.sum(~np.isnan(p),axis=1)

class strategy:
    def __init__(self, pop_size, genome_size, srate, mrate):
        self.n = pop_size
        self._max_l = genome_size
        self.srate = srate
        self.mrate = mrate

    def generate_from_lengths (self, ls):
        return np.stack( [random_padded_individual(l,self._max_l) for l in ls])
    
    def cut_matrix(self, _n):
        return np.stack( [rpad(np.ones(l),self._max_l) for l in np.random.randint(MIN_L,self._max_l,size=_n)])

    def init(self):
        individual_lengths = np.random.randint(MIN_L, self._max_l, size=self.n)
        individual_fitnesses = np.full(self.n,np.nan)
        individual_genotypes = self.generate_from_lengths(individual_lengths)
        return individual_lengths, individual_fitnesses, individual_genotypes

    def _x(self, a,b):
        c = np.concatenate([a,b],axis=1)
        def f(row):
            r = row[~np.isnan(row)]
            return rpad(r, self._max_l) if len(r) < self._max_l else r[:self._max_l]
        return np.apply_along_axis(f, 1, c)

    def X(self,pool):
        chromosomes = pool * self.cut_matrix(len(pool))
        split = int(len(pool) / 2) # it should be known that this is div by 2
        return np.concatenate([self._x(chromosomes[split:], chromosomes[:split]),
                               self._x(chromosomes[:split], chromosomes[split:])])

    def selection(self,individuals, return_pscores=False):
        K = int(self.srate*self.n) 
        mates = 2*int(self.n-K)
        replacement = self.n-mates
        scores = individuals[:,1] #1 is the index of scores on the ind matrix
        
        #correction just in case - scale everything but the truncated max
        #fitness function should avoid returrning this sort of thing
        #scores[~np.isfinite(scores)] = 1000# temp hard coded for all nan case?? scores[np.isfinite(scores)].max()
        
        scores = scores - scores.max() #minimise
        scores = scores / scores.sum() #normalize
        
        if return_pscores: return scores
        
        selected = np.random.choice(range(self.n),mates+replacement,p=scores) 
        return selected[:mates], selected[mates:]

    def mutations(self, rate):
        mar = np.zeros(self.n*self._max_l)
        idx = np.random.randint(self.n*self._max_l, size=int(self.n*self._max_l*self.mrate))
        mar[idx]= np.random.randint(CODON_MAX, size=len(idx))
        return mar.reshape((self.n,self._max_l))
    
    def select_and_mutate(self, meta, genes):
        pool_idx,replace_idx = self.selection(meta)
        return np.concatenate([genes[replace_idx], self.X(genes[pool_idx])]) + self.mutations(self.mrate)

class chain:
    def __init__(self,l=None, max_wraps=3, default_length=30): 
        if l is None: l = np.random.randint(0,10,default_length)
        l = np.concatenate([l[~np.isnan(l)].astype(int) for i in range(max_wraps)])
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
        if cn ==None: raise MappingException("mapping exception")
        return choices[cn % len(choices)] if len(choices) > 1 else choices[0]
    
    