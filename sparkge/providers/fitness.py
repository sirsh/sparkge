#from scipy import *
import numpy as np
from scipy import optimize

def regressor_fitness(mat_query_func,options,norm=xnorm):
    def _fitness(f_of_mat):
        mat = mat_query_func()
        X = mat[:,0:-1]
        Y = mat[:,-1]
        Y_dash = f_of_mat(X) 
        return norm(Y,Y_dash)
    return _fitness
	

def fitTheFunction(curve_fit_function, datax, datay, p0, display=False):
    out =  optimize.curve_fit(curve_fit_function,datax,datay,maxfev=5000, full_output =True,p0=p0)#,p0=p0   
    pfinal, covar = out[0], out[1]
    index,amp = pfinal[1],pfinal[0] 
    indexErr,ampErr = sqrt( covar[0][0] ) , sqrt( covar[1][1] ) * amp
    return (amp,ampErr), (index,indexErr), pfinal #<-- all pfinal data
	
	
#_fitted = func(xdata, 
#                       a[0],b[0],
#                       1  if l < 3 else all_params[2] ,
#                       1  if l < 4 else all_params[3],
#                       1  if l < 5 else all_params[4],
#                      )
#    
#        ss_res = np.sum((ydata - _fitted) ** 2)
#        ss_tot = np.sum((ydata - np.mean(ydata)) ** 2)
#        r2 = 1 - (ss_res / ss_tot)