from functools import wraps
from operator import *
from math import *
from . import MappingException

#info = [], F = var(chain(),info) -> call F(X=, Y=)
def terminal(original_function=None, is_constant=False):
    def _decorate(function):      
        choices = function()  
        def _terminal(genome,info=None):
            v = genome.choose(choices)
            def __terminal(**kwargs):
                if is_constant==False and info != None and v not in info:info.append(v)
                return kwargs[v]
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
                args = [f(genome,info) for f in exp_args] 
                op = genome.choose(choices)
                def ___op(**kwargs): #f(X,a,b,c,d)
                    invoked = [f(**kwargs) for f in args]  
                    return op(*invoked)
                return ___op
            return __op
        return _op
    if original_function: return _decorate(original_function)
    return _decorate

def as_expression(genome, f):
    try: 
        expressed = f(genome,args)
        def _f(**kwargs): return expressed(**kwargs)
        return _f
    except MappingException as mex: 
        def _f(**kwargs): return np.nan
        return _f
    

#signature modifier - switch from named args ot ordered args e.g. for curve fit
def accepting_ordered_params(f,params):
    def _f(*args):
        ordered_args = dict(zip(params,args))
        return f(**ordered_args)
    return _f      

#string representation of symbols
def _get_dict_(F) : return dict(zip(F.__code__.co_freevars, (c.cell_contents for c in F.__closure__)))
def _repr_(f):
    d = _get_dict_(f)
    if "expressed" in list(d.keys()):  return "{}".format(_repr_(d["expressed"]))
    elif "op" in list(d.keys()):
        op = d["op"].__name__
        if op == "sub":  return "({} - {})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op == "add":  return "({} + {})".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        if op == "mul":  return "{} * {}".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
        else:  return "{} / {}".format(_repr_(d["args"][0]),  _repr_(d["args"][1]))
    if "f" in d: return _repr_(d["f"])
    else:   return d["v"]
    
#simple evaluation sample    
def evaluate(population, target_function= lambda x : x*x, sample_x=list(range(4,10))):
    #move thes out?
    def __express_symbol__(x):
        def _f_(row): return expr(chain(row))(X=x)
        return _f_
    
    def __print_symbol__(row):
        try: return repr(sympify(_repr_(expr(chain(row)))))
        except: return None
    
    df_res = pd.DataFrame(index=range(len(population)))
    df_res["type"] = "result"
    df_tar = pd.DataFrame(index=range(len(population)))
    df_tar["type"] = "target"
    
    for x in sample_x: df_res[str(x)] = np.apply_along_axis(__express_symbol__(float(x)), 1, individual_genotypes)
    for x in sample_x: df_tar[str(x)] = target_function(x)
        
    df = pd.concat([df_res,df_tar])
    df= df.pivot(df.index, "type")
    df.columns = df.columns.swaplevel(0, 1)
    df.sortlevel(0, axis=1, inplace=True)
    df["error"] = np.abs(df["result"].fillna(np.inf) - df["target"]).sum(axis=1)
    df["repr"] = np.apply_along_axis(__print_symbol__, 1, individual_genotypes)
    return df
