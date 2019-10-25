import os

import panel as pn
from panel import widgets
import param
from dashboard_server.database_connector import DataBaseManager

WIDGET_WIDTH = 100
class PlotManager(param.Parameterized):
    db_manager = DataBaseManager()
    endpoint = widgets.TextInput(name="Server endpoint", value="http://localhost:8000/")
    url_widget = widgets.TextInput(width=300)
    extra = widgets.TextInput(name="Extra parameters")
    datasource = widgets.Select(name="Data source", width=200)
    x_val = widgets.Select(name="Plot x", width=WIDGET_WIDTH)
    y_val = widgets.Select(name="Plot y", width=WIDGET_WIDTH)
    z_val = widgets.Select(name="Plot z", width=WIDGET_WIDTH)
    color = widgets.Select(name="Color", width=WIDGET_WIDTH)
    size = widgets.Select(name="Size", width=WIDGET_WIDTH)
    button = widgets.Button(name="Test query", width=WIDGET_WIDTH)
    display = pn.pane.HTML(width=800, height=600)
    
    def __init__(self):
        self.populate_datasources()
        self.populate_widgets()

    @param.depends("datasource.value", "x_val.value", "y_val.value", "z_val.value",
                   "color.value", "size.value", "endpoint.value", "extra.value")
    def _url(self):
        url = self._get_url()
        
        self.url_widget.value = url
        
        return pn.pane.Str("")
    
    @param.depends("button.clicks", watch=True)
    def _update_iframe(self):
        iframe = ('<iframe width="800" height="600" scrolling="yes" frameBorder="0"'
                  'scrolling="no" src="{}"></iframe>'
                 ).format(self.url_widget.value)
        self.display.object = iframe

    def _get_url(self):
        url = "%s?" % self.endpoint.value
        ds_str = "datasource=%s&" % self.datasource.value
        url += "" if self.datasource.value is None else ds_str
        url += "" if self.x_val.value is None else "x=%s" % self.x_val.value
        url += "" if self.y_val.value is None else "&y=%s" % self.y_val.value
        url += "" if self.z_val.value is None else "&z=%s" % self.z_val.value
        url += "" if self.color.value is None else "&color=%s" % self.color.value
        url += "" if self.size.value is None else "&size=%s" % self.size.value
        url += "" if self.extra.value is None else "&%s" % self.extra.value
        return url
    
    @param.depends("db_manager.connect_btn.clicks", watch=True)
    def populate_datasources(self):
        if self.db_manager.connected:
            datasources = [None] + list(sorted(self.db_manager.get_table_names()))
            self.datasource.options = datasources
            
        return pn.pane.Str()
    
    @param.depends("datasource.value", watch=True)
    def populate_widgets(self):
        if self.db_manager.connected:
            columns = list(sorted(self.db_manager.get_column_names(self.datasource.value)))
            self.x_val.options = [None] + columns
            self.y_val.options = [None] + columns
            self.z_val.options = [None] + columns
            self.color.options = [None] + columns
            self.size.options = [None] + columns
        return pn.pane.Str()

    @property
    def url(self):
        return self._get_url()
    
    def panel(self):
        controls = pn.Column(pn.Row(self.datasource, self.endpoint), 
                             pn.Row(self.x_val, self.y_val, self.z_val, self.db_manager.connect_btn), 
                             pn.Row(self.color, self.size, self.extra))
        plot_dash = pn.Column(pn.pane.Markdown("# Plot manager"), controls,
                              pn.Row(self.button, pn.pane.Markdown("**Target url**"), self.url_widget),
                              self.display, self.populate_widgets, self.populate_datasources,
                              self._url, self._update_iframe)
        return plot_dash
        return pn.Tabs(("Plot manager", plot_dash), ("DB connection", self.db_manager.panel()))

os.environ["BOKEH_ALLOW_WS_ORIGIN"] = "*"
pn.extension()
ph = PlotManager()
ph.panel().servable()
