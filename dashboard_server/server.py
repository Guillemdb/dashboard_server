import io
import panel
import holoviews as hv
import pandas as pd
import hvplot.pandas
from flask import Flask, request, url_for
import time
import requests
import subprocess
from sqlalchemy import create_engine

app = Flask(__name__)
hv.extension("bokeh")
panel.extension()

GRAPH_PLOT_PATH = "/dashboard_server/apps/graph_plot/graph_plot.ipynb"
DATASOURCES_GUI_PATH = "/dashboard_server/apps/load_data/connect_to_db.py"


def get_datasource(name: str):
    engine = create_engine("postgresql://superset:superset@localhost:5432/superset")
    sql = "SELECT * \nFROM {}\nLIMIT 10000".format(name)
    df = pd.read_sql(sql, engine)
    return df


def parse_args(args):
    def parse_one(v):
        try:
            return eval(v)
        except:
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


@app.route("/embeddings", methods=["GET"])
def embeddings_page():
    args = dict(request.args)
    df = get_datasource(args["datasource"])
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(plot_embeddings(df, **args))
    return panel_to_html(pn)


@app.route("/hvplot", methods=["GET"])
def hvplot_page():
    hv.extension("bokeh")
    df = get_datasource(request.args["datasource"])
    args = dict(request.args)
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(df.hvplot(**args))
    return panel_to_html(pn)


@app.route("/scatter3d", methods=["GET"])
def scatter3d_page():
    df = get_datasource(request.args["datasource"])
    args = dict(request.args)
    del args["datasource"]
    args = parse_args(args)
    pn = panel.panel(scatter_3d(df, **args))
    return panel_to_html(pn)


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


@app.route("/", methods=["GET"])
def print_site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    msg = "Available Endpoints: <br> "
    for k, v in links:
        msg += "{} : {}<br>".format(k, v)
    return msg


@app.route("/site_map", methods=["GET"])
def get_site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    return {k: v for k, v in links}


def _run_app(port, app_name, path):
    app_path = "http://localhost:{}/{}".format(port, app_name)
    iframe = (
        '<iframe width="100%" height="100%" seamless frameBorder="0" scrolling="no"'
        ' src="{}"></iframe>'
    ).format(app_path)
    try:
        response = requests.get(app_path)
        if response.status_code == 200:
            return iframe
    except Exception as e:
        pass
    subprocess.Popen(["panel", "serve", path, "--port", str(port)])

    return iframe


@app.route("/run", methods=["GET"])
def run_app_page():
    args = dict(request.args)
    path = args["path"]
    port = args["port"]
    app_name = path.split("/").split(".")[0]

    iframe = _run_app(port, app_name, path)
    time.sleep(args.get("sleep", 1))
    return iframe


@app.route("/graph_plot", methods=["GET"])
def graph_plot():
    app_path = "http://localhost:5007"  # Change to local/public ip to expose
    iframe = (
        '<iframe width="100%" height="100%" seamless frameBorder="0" scrolling="no"'
        ' src="{}"></iframe>'
    ).format(app_path)
    return iframe


@app.route("/database", methods=["GET"])
def database_widget():
    app_path = "http://localhost:5006"  # Change to local/public ip to expose
    iframe = (
        '<iframe width="100%" height="100%" seamless frameBorder="0" scrolling="no"'
        ' src="{}"></iframe>'
    ).format(app_path)
    return iframe


if __name__ == "__main__":
    print(
         "Opening single process Flask app with embedded Bokeh application on "
         "http://localhost:8000/"
    )
    print()
    print("Multiple connections may block the Bokeh app in this configuration!")
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    _run_app(port=5006, app_name="parquet2sqlGUI", path=DATASOURCES_GUI_PATH)
    _run_app(port=5007, app_name="graph_plot", path=GRAPH_PLOT_PATH)
    app.run(port=8000, host="0.0.0.0")

