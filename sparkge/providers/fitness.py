from scipy import optimize
import numpy as np

def summarise(df_view):
    grp = df_view.groupby(df_view.index)
    return grp.mean().join(grp.std()/np.sqrt(grp.count()), rsuffix="err")

def goodness_of_fit(model, data, estimate):
    #check cov and the like - if its wild return 0 or whatever is bad
    x_col = data.columns[0]
    ydata = data[x_col].values
    fitted = model(data.index.values,*estimate[0])  
    
    ss_res = np.sum((ydata - fitted) ** 2)
    ss_tot = np.sum((ydata - np.mean(ydata)) ** 2)
    res=(ss_res / ss_tot) 
    return res

def curve_fit(model,data,estimate,display=False):
    x_col = data.columns[0]
    err_col = x_col+"err"
    summary = summarise(data)
    _data = data.join(summary[[err_col]])
    estimate =  optimize.curve_fit(model,_data.index.values,_data[x_col].values, maxfev=1000, full_output=True, p0=estimate[0],sigma=_data[err_col])
    #print(estimate[0])
    full_fitted_vals =  model(summary.index.values,*estimate[0])  
    
    if display:
        summary["fit"] = full_fitted_vals
        summary[[x_col, "fit"]].plot()
    
    return estimate
    