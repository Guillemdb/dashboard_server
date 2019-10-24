from panel import widgets
import panel
import param
from sqlalchemy import create_engine


class DataBaseManager(param.Parameterized):
    file_input = widgets.FileInput(name="Parquet file")
    dbtype = widgets.TextInput(name="Database type", value="postgresql")
    user = widgets.TextInput(name="Username", value="superset")
    password = widgets.TextInput(name="Password", value="superset")
    host = widgets.TextInput(name="Host", value="localhost")
    endpoint = widgets.TextInput(name="Host", value="superset")
    port = widgets.LiteralInput(name="Port", value=5432)
    connect_btn = widgets.Button(name="Connect to DB")
    data_source = widgets.TextInput(name="Table")
    datasource_btn = widgets.Button(name="Query table")

    def __init__(self):
        super().__init__()
        self.df = None
        self.datasource = None
        self.engine = None
        self._connected = False

    @property
    def url(self):
        url = "{}://{}:{}@{}:{}/{}".format(
            self.dbtype.value,
            self.user.value,
            self.password.value,
            self.host.value,
            self.port.value,
            self.endpoint.value,
        )
        return url

    @param.depends("connect_btn.clicks", watch=True)
    def connect_to_db(self):
        msg = panel.pane.Str("Connected to \n{}".format(self.url))
        if self.connect_btn.clicks == 0:
            return panel.pane.Str("Ready to connect to \n{}".format(self.url))
        if self._connected:
            return msg
        try:
            engine = create_engine(self.url)
            self.engine = engine
            self._connected = True
            return msg
        except Exception as e:
            self._connected = False
            return panel.pane.Str("Error connecting to database \n{}".format(self.url))

    def panel(self):
        widgets = panel.Row(
            panel.Column(self.dbtype, self.host, self.port),
            panel.Column(self.user, self.password, self.endpoint),
            panel.Column(self.connect_to_db, self.connect_btn),
        )
        return panel.Column(panel.pane.Markdown("## Connect to superset database"), widgets)