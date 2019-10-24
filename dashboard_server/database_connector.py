from panel import widgets
import panel
import param
from sqlalchemy import create_engine

WIDGET_WIDTH = 100


class DataBaseManager(param.Parameterized):
    file_input = widgets.FileInput(name="Parquet file")
    dbtype = widgets.TextInput(name="Database type", value="postgresql", width=WIDGET_WIDTH)
    user = widgets.TextInput(name="Username", value="superset", width=WIDGET_WIDTH)
    password = widgets.TextInput(name="Password", value="superset", width=WIDGET_WIDTH)
    host = widgets.TextInput(name="Host", value="localhost", width=WIDGET_WIDTH)
    endpoint = widgets.TextInput(name="Host", value="superset", width=WIDGET_WIDTH)
    port = widgets.LiteralInput(name="Port", value=5432, width=WIDGET_WIDTH)
    data_source = widgets.TextInput(name="Table Name", width=WIDGET_WIDTH)
    connect_btn = widgets.Button(name="Connect to DB", width=WIDGET_WIDTH)
    datasource_btn = widgets.Button(name="Query table", width=WIDGET_WIDTH)

    def __init__(self):
        super().__init__()
        self.df = None
        self.datasource = None
        self.engine = None
        self._connected = False

    @param.depends("dbtype.value", "user.value", "password.value",
                   "host.value", "port.value", "endpoint.value")
    def _url(self):
        return panel.pane.Str(self._get_url())

    def _get_url(self):
        url = "{}://{}:{}@{}:{}/{}".format(
            self.dbtype.value,
            self.user.value,
            self.password.value,
            self.host.value,
            self.port.value,
            self.endpoint.value,
        )
        return url

    @property
    def url(self):
        return self._get_url()

    @param.depends("connect_btn.clicks", watch=True)
    def connect_to_db(self):
        msg = panel.Column(panel.pane.Str("Connected to"), self._url)
        if self.connect_btn.clicks == 0:
            return panel.Column(panel.pane.Str("Ready to connect to"), self._url)
        if self._connected:
            return msg
        try:
            engine = create_engine(self.url)
            self.engine = engine
            self._connected = True
            return msg
        except Exception as e:
            self._connected = False
            return panel.Column(panel.pane.Str("Error connecting to"), self._url)

    def panel(self):
        widgets = panel.Row(
            panel.Column(self.dbtype, self.host, self.port),
            panel.Column(self.user, self.password, self.endpoint),
            panel.Column(self.connect_to_db, self.connect_btn),
        )
        return panel.Column(panel.pane.Markdown("## Connect to superset database"), widgets)