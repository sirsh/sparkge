"""
Symbols.py show a general pattern for gene expression using closures and decorators.
This is currently focused on symbolic regression but the principles are general. 
Terminals, operators and expressions are intended to be general structural elements to which any grammar/fuctions can be applied
As I am focusing on regression only I have not tried to test for generality however this file should be treated like a general pattern for future.
"""
from functools import wraps
from operator import *
from math import *
import numpy as np
import pandas as pd

from . import MappingException
from . evolution import chain

from sympy import sympify
from sympy import init_printing

#info = [], F = var(chain(),info) -> call F(X=, Y=)
def terminal(original_function=None, is_constant=False):
    def _decorate(function):      
        choices = function()  
        def _terminal(genome,info=None):
            v = genome.choose(choices)
            def __terminal(**kwargs):
                if is_constant==False and info != None and v not in info:info.append(v)
                return kwargs[v] if v in kwargs else np.nan
            return __terminal
        return _terminal
    if original_function: return _decorate(original_function)
    return _decorate

#B = bop(exp,exp),B=B(c),B(X=1)
def operator(original_function=None):
    def _decorate(function):      
        choices = function()  
        def _op(*exp_args):          #f(exp,exp)->operator of cardinality
            def __op(genome,info=None):         #f(chain)->expression 
                #print("expanding op")
                op = genome.choose(choices) #order can be pre or otherwise
                args = [f(genome,info) for f in exp_args] 

                def ___op(**kwargs): #f(X,a,b,c,d)
                    invoked = [f(**kwargs) for f in args]  
                    return op(*invoked)
                return ___op
            return __op
        return _op
    if original_function: return _decorate(original_function)
    return _decorate

def as_expression(genome, choices, args=[]):
    try: 
        #print("expanding expression")
        f  = genome.choose(choices)
        expressed = f(genome,choices)
        def _f(**kwargs): return expressed(**kwargs)
        return _f
    except MappingException as mex: 
        def _f(**kwargs): return np.nan
        return _f
    
#signature modifier - switch from named args ot ordered args e.g. for curve fit
def accepting_ordered_params(f, idpvars=["X"]):
    """
    Example modification of signature to suit certain calling approaches. 
    Numerical libraries for example will optimize a function f(X, *params)
    This is a work in progress
    """
    def _f(*args):
        S = display(f)
        #convention for now - tbd... what is best for passing to fitting routines?
        _set = set([str(c) for c in S.free_symbols])
        param_names =list( _set - set(idpvars) )
        param_names.sort()
        if "X" in _set:  param_names = idpvars + param_names

        ordered_args = dict(zip(param_names,args))
        return f(**ordered_args)
    return _f      

#string representation of symbols
def _get_dict_(F) :
    #todo the last line needs to check for python version 2 or 3 and use a slightly different syntax
    if F == None or F.__closure__ == None: return {}
    return dict(zip(F.__code__.co_freevars, (c.cell_contents for c in F.__closure__)))

#this is a hard coded thing that could work better with the python/math operators 
def _repr_(f):
    d = _get_dict_(f)
    if "expressed" in list(d.keys()):  return "{}".format(_repr_(d["expressed"]))
    elif "op" in list(d.keys()):
        op = d["op"].__name__
        if op == "sub":  return "({}-{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op == "add":  return "({}+{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op == "mul":  return "({}*{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op == "truediv":  return "({}/{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op in ["log", "exp", "sin", "cos"]: return "({}({}))".format(op,  _repr_(d["args"][0]))
        if op in ["squared"]: return "({}**2)".format(_repr_(d["args"][0]))
        if op in ["cubed"]: return "({}**3)".format(_repr_(d["args"][0]))
        if op in ["power"]: return "({}**{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        else:  
            print("not handled", d) #printing for debug becasue often this suggest not handled
            return "({}/{})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
    if "f" in d: return _repr_(d["f"])
    elif "v" in d: return d["v"]
    else: return None
    
def display(f,printer='mathjax'):
    """
    Converts to a sympy form which has a nice display format, simplification and other features
    """
    init_printing(use_latex=printer)
    try:
        return sympify(_repr_(f))
    except:
        return np.nan #temp cheat
    
#plot symbol - todo
#plt.plot([S(_x, *popt) for _x in x])

#show tree - todo
#simple evaluation sample    
def _evaluate(population, _symbol, target_function= lambda x : 2*x*x- x**3+x**4, sample_x=list(range(4,7)), return_all=False):
    """
    The evaluation against a passed in target function plus alot of boilerplate
    """
    def __express_symbol__(x):
        def _f_(row): 
            try:  return _symbol(chain(row))(X=x)
            except: return np.inf#e.g. division by zero
        return _f_
    
    def __print_symbol__(row): return repr(display(_symbol(chain(row))))
    
    df_res = pd.DataFrame(index=range(len(population)))
    df_res["type"] = "result"
    df_tar = pd.DataFrame(index=range(len(population)))
    df_tar["type"] = "target"
    
    for x in sample_x: df_res[str(x)] = np.apply_along_axis(__express_symbol__(float(x)), 1, population)
    for x in sample_x: df_tar[str(x)] = target_function(x)
        
    df = pd.concat([df_res,df_tar])
    df= df.pivot(df.index, "type")
    df.columns = df.columns.swaplevel(0, 1)
    df.sortlevel(0, axis=1, inplace=True)
    df["error"] = np.abs(df["result"].fillna(np.inf) - df["target"]).sum(axis=1)
    #df["repr"] = np.apply_along_axis(__print_symbol__, 1, individual_genotypes)
    if return_all: return df
    return df["error"].values

def _evaluate_against_data(genes, _symbol, data,p0):
    """
    The evaluation against a dataset plus alot of boilerplate
    Fitness functions are called in from the providers/ module e.g. to fit a curve and test it's goodness of fit
    """
    from . providers.fitness import curve_fit, goodness_of_fit
    
    def fit_symbol(S, data, p0):
        #assert p0 is list of list (for now)
        try:
            if not display(S).has("X"):return np.random.uniform(1,100) # needs to be a function of X - will clean up the interface later
            S = accepting_ordered_params(S)
            result = curve_fit(S,data,p0)
            loss = goodness_of_fit(S, data, result)
            if loss < 0 or loss > 1:
                return np.random.uniform(200,300)# temp until i understand the scales
            #print("evaluated", str(S))
            return loss
        except Exception as ex:  #for any reason i.e. S is a nan, S is null, optimsation error
            #print(repr(ex))
            return np.random.uniform(1000,2000)
    def _fit_(row): return fit_symbol(_symbol(chain(row)),data,p0=p0)  
    return np.apply_along_axis(_fit_,1,genes)

