import io
import panel
import holoviews as hv
import pandas as pd
import hvplot.pandas
from flask import Flask, request
import time
import requests
import subprocess
from sqlalchemy import create_engine

app = Flask(__name__)
hv.extension("bokeh")
panel.extension()

GRAPH_PLOT_PATH = "/home/guillem/github/dashboard_server/apps/graph_plot/graph_plot.ipynb"

def get_datasource(name: str):
    engine = create_engine("postgresql://superset:superset@localhost:5432/superset")
    sql = "SELECT * \nFROM {}\nLIMIT 10000".format(name)
    df = pd.read_sql(sql, engine)
    return df


def parse_args(args):
    def parse_one(v):
        if v == "None":
            return None
        try:
            v = float(v)
            v = int(v) if int(v) == v else v
        except:
            return v
        try:
            v = eval(v)
        except:
            return v
        return v
    return {k: parse_one(v) for k, v in args.items()}


def panel_to_html(data, *args, **kwargs):
    f = io.StringIO()
    data.save(f, *args, **kwargs)
    f.seek(0)
    return f.read()


def plot_embeddings(df, x_0="x_0", x_1="x_1", **kwargs):
    hv.extension("bokeh")
    scatter = hv.Scatter(df, kdims=[x_0, x_1]).opts(tools=["hover"], **kwargs)
    return scatter


def scatter_3d(df, x, y, z, **args):
    hv.extension("plotly")
    return hv.Scatter3D(df, kdims=[x, y, z]).opts(**args)


@app.route('/embeddings', methods=['GET'])
def embeddings_page():
    args = dict(request.args)
    df = get_datasource(args["datasource"])
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(plot_embeddings(df, **args))
    return panel_to_html(pn)


@app.route('/hvplot', methods=['GET'])
def hvplot_page():
    hv.extension("bokeh")
    df = get_datasource(request.args["datasource"])
    args = dict(request.args)
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(df.hvplot(**args))
    return panel_to_html(pn)


@app.route('/scatter3d', methods=['GET'])
def scatter3d_page():
    df = get_datasource(request.args["datasource"])
    args = dict(request.args)
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(scatter_3d(df, **args))
    return panel_to_html(pn)

@app.route('/run', methods=['GET'])
def run_app_page():
    args = dict(request.args)
    path = args["path"]
    port = args["port"]
    app_name = path.split("/").split(".")[0]

    app_path = "http://localhost:{}/{}".format(port, app_name)
    iframe = ('<iframe width="100%" height="100%" seamless frameBorder="0" scrolling="no"'
              ' src="{}"></iframe>').format(app_path)
    try:
        response = requests.get(app_path)
        if response.status_code == 200:
            return iframe
    except Exception as e:
        pass
    subprocess.Popen(['panel', 'serve', path, '--port', str(port)])
    time.sleep(args.get("sleep", 1))
    return iframe

@app.route('/graph_plot', methods=['GET'])
def run_node():
    args = dict(request.args)
    path = GRAPH_PLOT_PATH
    port = args["port"]
    app_name = "graph_plot"

    app_path = "http://localhost:{}/{}".format(port, app_name)
    iframe = ('<iframe width="100%" height="100%" seamless frameBorder="0" scrolling="no"'
              ' src="{}"></iframe>').format(app_path)
    try:
        response = requests.get(app_path)
        if response.status_code == 200:
            return iframe
    except Exception as e:
        pass
    subprocess.Popen(['panel', 'serve', path, '--port', str(port)])
    time.sleep(args.get("sleep", 1))
    return iframe


if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)