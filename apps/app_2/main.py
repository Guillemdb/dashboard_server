#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
os.environ["BOKEH_ALLOW_WS_ORIGIN"] = "*"

from itertools import product

import holoviews as hv
import numpy
import numpy as np
import pandas as pd
from seriate import seriate
from tqdm import tqdm_notebook as tqdm

from commit_time_series.similarity_metric import calculate_metrics, relativize_matrix
hv.extension("bokeh")


# In[2]:


df = pd.read_csv("commits_for_distance.csv", index_col=0)
df["date_ix"] = df["date_ix"].map(pd.to_datetime)
df = df.set_index("date_ix")
df.index.name = "Date"


# In[3]:


def get_metrics_matrix(commits: pd.DataFrame) -> numpy.ndarray:
    """Build a numpy array containing the upper triangular distance metrics."""
    n_developers = len(df.columns)
    distance_matrix = numpy.zeros((n_developers, n_developers))
    entropy_matrix = numpy.zeros((n_developers, n_developers))
    norm_matrix = numpy.zeros((n_developers, n_developers))
    shift_matrix = numpy.zeros((n_developers, n_developers))
    num_values_matrix = numpy.zeros((n_developers, n_developers))
    indexed_names = set(enumerate(commits.columns))
    for row in tqdm(list(product(indexed_names, indexed_names))):
        x_i, y_i = row[0][0], row[1][0]
        if x_i < y_i: 
            dev_x, dev_y = row[0][1], row[1][1]
            x, y = df[dev_x].values, df[dev_y].values
            (distance, entropy, norm, shift_metric, num_score) = calculate_metrics(x, y)
            distance_matrix[x_i, y_i] = distance_matrix[y_i, x_i] = distance
            entropy_matrix[x_i, y_i] = entropy_matrix[y_i, x_i] = entropy
            norm_matrix[x_i, y_i] = norm_matrix[y_i, x_i] = norm
            shift_matrix[x_i, y_i] = shift_matrix[y_i, x_i] = shift_metric
            num_values_matrix[x_i, y_i] = num_values_matrix[y_i, x_i] = num_score

    distance_normed = relativize_matrix(distance_matrix)
    entropy_normed = relativize_matrix(entropy_matrix)
    norm_normed = relativize_matrix(norm_matrix)
    shift_normed = relativize_matrix(shift_matrix)
    num_values_normed = relativize_matrix(num_values_matrix)
    return distance_normed, entropy_normed, norm_normed, shift_normed, num_values_normed

def combine_metrics(metrics, shift_weight, numvals_weight):
    distance, entropy, norm, shift, num_values = metrics
    score = distance * entropy * norm
    final = score * shift ** shift_weight * num_values ** numvals_weight
    return seriate(final)

def format_columns(cols):
    return [c[:30] for c in cols]


def plot_commit_heatmap(commits,
                        width=900, height=400, 
                        resample=None, xlabel=None, title="Seriated heatmap", cmap="viridis"):
    xlabel = xlabel if xlabel is not None else commits.index.name
    xlabel = "index" if xlabel is None else xlabel
    commits = commits if resample is None else commits.resample(resample).sum()
    commits.index = [x.strftime("%D") for x in commits.index]
    mat = commits.values.T
    mat = mat / mat.max(axis=1)[:, None]
    heatmap = hv.HeatMap({'x': commits.index,
                          'y': format_columns(commits.columns),
                          'z': mat.round(3)*100}, 
                          kdims=[('x', xlabel), ('y', 'Identity')], 
                          vdims=('z', "% With respect to max"))
    heatmap= heatmap.opts(cmap="viridis", width=width, height=width,fontsize={'xticks': '2pt'},
                          tools=["hover"], xrotation=90, title=title)
    return heatmap

def seriate_df(df, metrics, shift_weight: float=0.1,
                            numvals_weight: float=0.25):
    seriation = combine_metrics(metrics, shift_weight, numvals_weight)
    df = df.iloc[:, seriation]
    return df
    


# In[4]:


metrics = get_metrics_matrix(df)


# In[5]:



    
def heatmap_plus_series(df, cmap="fire", width=1100, height=700, *args, **kwargs):
    # Declare Tap stream with heatmap as source and initial values
    
    heatmap = plot_commit_heatmap(df,cmap=cmap, *args, **kwargs)#.opts(xticks=None)
    #posxy = hv.streams.Tap(source=heatmap, x=df.index.values[0], y=df.columns.values[0])
    posxy = hv.streams.BoundsY(source=heatmap, boundsy=(0, 1))
    polys = hv.Polygons([])
    box_stream = hv.streams.BoxEdit(source=polys)
    # Define function to compute histogram based on tap location
    def select_series(boundsy):
        test = df.columns.values[0] == boundsy[0]
        def plot_series(df, i):
            data = {"x": df.index.values, "y": df.iloc[:, i].values}
            return hv.Area(data) #* hv.Curve(data).opts(tools=["hover"])
        low, high = boundsy
        low, high = int(np.floor(low)), int(np.ceil(high))
        overlay = hv.NdOverlay({df.columns[i] : hv.Area(df.iloc[:, i].values) 
                                                #* hv.Curve(df.iloc[:, i].values).opts(tools=["hover"]))
                                for i in range(low, high)}).opts(legend_position='left',
                                                                 fontsize={'legend': '6pt'})
        ticks = list(zip(range(len(df.index)), [pd.to_datetime(x).strftime("%Y-%m-%d") for x in df.index]))
        return   hv.Area.stack(overlay.opts(xticks=ticks[::len(df.index) // 15],
                                            ylim=(0, None),#df.iloc[:, list(range(low,high))].values.max()*1.05),
                                            xlabel="Date", ylabel="Commits", xrotation=45))
    
    tap_dmap = hv.DynamicMap(select_series, streams=[posxy])
    h_opts =hv.opts.HeatMap(cmap=cmap, fontsize={'xticks': '6pt'}, height=height,
                     logz=True, tools=['hover'], width=width, xrotation=90)
    c_opts = hv.opts.Area(framewise=False, height=300, width=width, yaxis='right',
                          )
    
    plot = (heatmap + tap_dmap).cols(1).opts(h_opts, c_opts)
    
    return plot
                                             
def filter_metrics(metrics, df, cols):
    dfs = [pd.DataFrame(data=met, index=df.columns, columns=df.columns) for met in metrics]
    _metrics = [_df.loc[cols, cols] for _df in dfs]
    return [met.values for met in _metrics]
    

def metaplot(shift_weight: float=0.1,
            numvals_weight: float=0.25,
            resample: str=None,
            dates: tuple=None,
            columns: list=None):
    
    small = df.loc[dates[0]:dates[1]].copy() if dates is not None else df
    if len(columns) > 3:
        small = small.loc[:, columns]   
        col_mask = np.array([c in columns for c in df.columns])
        mets = filter_metrics(metrics, df, columns)
    else:
        mets = metrics
    
    
    seriated = seriate_df(small, mets, shift_weight=shift_weight, numvals_weight=numvals_weight)
    return heatmap_plus_series(seriated, resample=resample)
            


# In[6]:


from functools import partial
import hvplot.pandas
import param
import panel as pn
from panel.interact import interact, interactive, fixed, interact_manual
from panel import widgets

shift = widgets.FloatSlider(start=0., end=5, step=0.1, value=0.1, name="Shift weight")
nums = widgets.FloatSlider(start=0., end=5, step=0.1, value=0.3, name="Values weight")
resample = widgets.LiteralInput(value=None, name="Resample")
resample = widgets.Select(options={"Day": "D", "Week": "W", "Month":"M"})
columns = widgets.MultiSelect(options=df.columns.values.tolist(), value=df.columns.values.tolist(), name="Series")
columns.height = 300
columns.width = 200

dates = widgets.DateRangeSlider(start=df.index[0], end=df.index[-1], name="Date range",
                                value=(df.index[0], df.index[-1]))
widget, plot = interact(metaplot, shift_weight=shift, numvals_weight=nums,
                        dates=dates, columns=columns, resample=resample)


# In[ ]:





# In[ ]:





# In[ ]:





# In[16]:



dashboard = pn.Row(pn.Column(plot), pn.Column(widget))


# In[15]:

if __name__ == "__main__":
	dashboard.servable()


# In[11]:





# In[ ]:


#pn.app("localhost:7777")


# In[ ]:


#pn.Row(pn.Column(widget[0], widget[1]), pn.Column(widget[2], widget[3]), pn.Column(widget[4]))


# In[ ]:


#plot


# In[ ]:





# In[ ]:




