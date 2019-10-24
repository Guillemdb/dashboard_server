import io
import os

import numpy
import panel
from panel import widgets
import param
import pandas
import pandas as pd
from dashboard_server.database_connector import DataBaseManager

try:
    from commit_time_series.data_export import deserialize_sparse_matrix
    from commit_time_series.seriation import Seriator
    from commit_time_series.extractor import Columns
except ImportError:
    pass

WIDGET_WIDTH = 100


class CommitTimeSeriesPreprocessor(param.Parameterized):

    EMBEDDINGS_TABLE = "developer_embeddings"
    COMMITS_TABLE = "commit_series"
    GROUPED_COMMITS_TABLE = "commits_per_repo"
    GROUPED_EMBEDDINGS_TABLE = "clusters_per_repo"
    embeddings_file = widgets.FileInput(name="Embeddings")
    commits_file = widgets.FileInput(name="Commits")
    grouped_file = widgets.FileInput(name="Grouped series")
    load_parquet_btn = widgets.Button(name="Load files", width=WIDGET_WIDTH)
    to_sql_btn = widgets.Button(name="Write to DB.", width=WIDGET_WIDTH)

    def __init__(self, engine):
        super(CommitTimeSeriesPreprocessor, self).__init__()
        self.embeddings = None
        self.grouped = None
        self.commits = None
        self.engine = engine
        self._data_loaded = False

    @staticmethod
    def extract_commits_per_repo(df):
        """
        Extract a DataFrame with columns ['date_ix', 'commits', 'name', 'repository'] \
        from grouped commit series data.
        """

        def get_one_commit_series(x):
            data = pandas.DataFrame(
                index=df.loc[0, Columns.Value],
                data=numpy.array(x[Columns.Value].todense()).flatten(),
                columns=[Columns.Value],
            )
            data.index.name = Columns.Date
            data = data.reset_index()
            data = data[data[Columns.Value] > 0]
            data[Columns.SeriesId] = x[Columns.SeriesId]
            data[Columns.Repository] = x[Columns.Repository]
            return data

        commit_series_per_repo = df.iloc[1:].apply(get_one_commit_series, axis=1)
        return pandas.concat(commit_series_per_repo.values)

    @staticmethod
    def extract_groups(df: pandas.DataFrame):
        data = df.loc[
            1:,
            [
                Columns.SeriesId,
                Columns.Repository,
                Seriator.CLUSTER,
                Seriator.SERIATED_IDX,
                "x_0",
                "x_1",
            ],
        ]
        return data

    @staticmethod
    def read_parquet(file_widget):
        f = io.BytesIO()
        f.write(file_widget.value)
        f.seek(0)
        return pd.read_parquet(f)

    def load_grouped_series(self, file_widget) -> pandas.DataFrame:
        """Load and deserialize the target parquet file containing encoded commit time series."""
        if file_widget.value is None:
            return None
        df = self.read_parquet(file_widget)
        start_date, end_date = df.loc[0, [Columns.SeriesId, Columns.Repository]].values.tolist()
        df.loc[:, Columns.Value] = df.loc[:, Columns.Value].astype(object)
        times = pandas.date_range(start_date, end_date, freq="D").values
        matrices = df.loc[1:, Columns.Value].map(deserialize_sparse_matrix).values.tolist()
        df.loc[:, Columns.Value] = [times] + matrices
        return df

    def read_parquet_files(self):
        grouped = self.load_grouped_series(self.grouped_file)
        embeddings = (
            self.read_parquet(self.embeddings_file)
            if self.embeddings_file.value is not None
            else None
        )
        commits = (
            self.read_parquet(self.commits_file) if self.commits_file.value is not None else None
        )
        return commits, embeddings, grouped

    @param.depends("load_parquet_btn.clicks", watch=True)
    def load_data(self):
        if self.load_parquet_btn.clicks == 0:
            return panel.pane.HTML("")
        dataframes = self.read_parquet_files()
        self.commits, self.embeddings, self.grouped = dataframes
        self._data_loaded = True
        return panel.pane.HTML(
            self.grouped.head().to_html() if self.grouped is not None else "No data loaded"
        )

    def preprocess_data(self):
        grouped_commits = self.extract_commits_per_repo(self.grouped)
        grouped_embeddings = self.extract_groups(self.grouped)
        commits_with_teams = self.commits.merge(
            self.embeddings, left_on="name", right_index=True, how="inner"
        )
        commits_with_teams = commits_with_teams.drop(["x_0", "x_1", "type_x"], axis=1)
        commits_with_teams = commits_with_teams.rename(columns={"type_y": "type"})

        return commits_with_teams, self.embeddings, grouped_commits, grouped_embeddings

    def to_sql(self, *args, **kwargs):
        commits, embeddings, grouped_commits, grouped_embeddings = self.preprocess_data()
        grouped_commits.to_sql(self.GROUPED_COMMITS_TABLE, self.engine, *args, **kwargs)
        grouped_embeddings.to_sql(self.GROUPED_EMBEDDINGS_TABLE, self.engine, *args, **kwargs)
        commits.to_sql(self.COMMITS_TABLE, self.engine, *args, **kwargs)
        embeddings.to_sql(self.EMBEDDINGS_TABLE, self.engine, *args, **kwargs)

    @param.depends("to_sql_btn.clicks", watch=True)
    def to_parquet(self):
        if self._data_loaded:
            mkdwn = "Created the following tables: \n"
            try:
                commits, embeddings, grouped_commits, grouped_embeddings = self.preprocess_data()
                grouped_commits.to_parquet(self.GROUPED_COMMITS_TABLE + ".parquet")
                mkdwn += "- {}\n".format(self.GROUPED_COMMITS_TABLE)
                grouped_embeddings.to_parquet(self.GROUPED_EMBEDDINGS_TABLE + ".parquet")
                mkdwn += "- {}\n".format(self.GROUPED_EMBEDDINGS_TABLE)
                commits.to_parquet(self.COMMITS_TABLE + ".parquet")
                mkdwn += "- {}\n".format(self.COMMITS_TABLE)
                embeddings.to_parquet(self.EMBEDDINGS_TABLE + ".parquet")
                mkdwn += "- {}\n".format(self.EMBEDDINGS_TABLE)
            except Exception as e:
                raise e
                pass
            return panel.pane.Str(mkdwn)
        else:
            return panel.pane.Str("")

    def panel(self):
        return panel.Column(
            panel.pane.Markdown("###Load eee-cts data into superset"),
            panel.Row(panel.pane.Str("Embeddings    "), self.embeddings_file),
            panel.Row(panel.pane.Str("Grouped Series"), self.grouped_file),
            panel.Row(panel.pane.Str("Commit Series "), self.commits_file),
            panel.Row(self.load_data),
            panel.Row(self.to_parquet),
            panel.Row(self.load_parquet_btn, self.to_sql_btn),
        )


class WriteParquet(param.Parameterized):
    write_btn = widgets.Button(name="Write to DB", width=WIDGET_WIDTH)
    read_btn = widgets.Button(name="Read DB table", width=WIDGET_WIDTH)
    parquet_file = widgets.FileInput(name="Parquet file", width=WIDGET_WIDTH)
    table = widgets.TextInput(name="New table name", width=200)
    table_names = widgets.Select(name="DB tables", width=200)

    def __init__(self, engine, *args, **kwargs):
        super(WriteParquet, self).__init__(*args, **kwargs)
        self.engine = engine
        self.df = None
        self.db_df = None

    @param.depends("parquet_file.value", watch=True)
    def load_parquet(self):
        f = io.BytesIO()
        f.write(self.parquet_file.value)
        f.seek(0)
        self.df = pd.read_parquet(f)

    @param.depends("read_btn.clicks", watch=True)
    def get_datasource(self):
        if self.data_source.value != "":
            sql = "SELECT * \nFROM {}\nLIMIT 10000".format(self.table.value)
            self.df = self.sql(sql)
        table = self.table.value if self.table.value != "" else "None"
        return panel.pane.Str("Selected Table {}".format(table))

    def sql(self, sql):
        df = pd.read_sql(sql, self.engine)
        return df

    def get_table_names(self):
        if self.engine is None:
            return
        names = pd.read_sql("SELECT tablename FROM pg_catalog.pg_tables;", self.engine)
        self.table_names.options = list(sorted(names.values.flatten().tolist()))

    @param.depends("write_btn.clicks", watch=True)
    def write_parquet(self):
        if self.write_btn.clicks > 0:
            try:
                self.load_parquet()
                self.df.to_sql(self.table.value, self.engine)
                return panel.pane.Str("Success")
            except Exception as e:
                return panel.pane.Str(str(e))
        return panel.pane.Str("")

    @param.depends("read_btn.clicks", watch=True)
    def read_table(self):
        if self.read_btn.clicks > 0:
            sql = "SELECT * \nFROM {}\nLIMIT 10000".format(self.table_names.value)
            self.db_df = self.sql(sql)
            return panel.pane.HTML(self.db_df.head().to_html())
        return panel.pane.Str()

    def panel(self):
        return panel.Row(
            panel.Column(
                panel.Row(self.table_names),
                panel.Row(panel.pane.Markdown("Parquet file"), self.parquet_file),
                panel.Row(self.table),
                panel.Row(self.read_btn, self.write_btn),

            ),
            panel.Column(self.read_table, self.write_parquet),
        )


class Dashboard(param.Parameterized):
    db_manager = DataBaseManager()
    parquet = WriteParquet

    def __init__(self):
        self.parquet = WriteParquet(self.db_manager)
        self.cts_loader = CommitTimeSeriesPreprocessor(self.db_manager)
        self.parquet.write_btn.disabled = True
        self.parquet.read_btn.disabled = True

    @param.depends("db_manager.connect_btn.clicks", watch=True)
    def update_engine(self):
        if self.db_manager.connect_btn.clicks > 0:
            self.parquet.engine = self.db_manager.engine
            self.parquet.write_btn.disabled = False
            self.parquet.read_btn.disabled = False
            self.parquet.get_table_names()
            self.cts_loader.engine = self.db_manager.engine

    @param.depends("parquet.write_btn.clicks", watch=True)
    def write_clicked(self):
        if self.parquet.engine is not None and self.parquet.write_btn.clicks > 0:
            self.parquet.get_table_names()

    def panel(self):
        return panel.Tabs(
            ("Database", self.db_manager.panel()),
            ("eee-cts", self.cts_loader.panel()),
            ("Parquet2sql", panel.Column(self.parquet.panel(), self.update_engine,
                                         self.write_clicked)),
        )


os.environ["BOKEH_ALLOW_WS_ORIGIN"] = "*"
panel.extension()
dash = Dashboard()
dash.panel().servable()
