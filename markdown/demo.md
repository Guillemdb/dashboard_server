# Introduction to dashboard_server

### Requirements

This demo runs in its own separate docker container, and all the required data to run them is provided
in the repository. However, we will require a mysql database to running on the system.

By default, it will connect to the [`sourced-ui`](https://github.com/src-d/sourced-ui) superset mysql database that [`sourced`](https://sourced.tech/get-started/) provides on the following url:

`postgresql://superset:superset@localhost:5432/superset`

In this tutorial we will forget about superset and run the tutorial using a web browser.

### Setting up the environment

Let's setup the Docker container of the demo, and run dashboard_server:

1. `docker build -t dashboard_server .`
2. `docker run --rm --network="host" -p 5006:5006 -p 8000:8000 -it dashboard_server:latest python3  dashboard_server/dashboard_server/server.py`

### Check that everything has been install properly

Go to [http://localhost:8000](http://localhost:8000) and check that the server displays all the different endpoints available.

<img src="../images/root_site_map.png" width="200" height="150" />

Please note that this demo only runs on http, not https for the sake of simplicity.

## Loading the data



We will load the data provided as parquet files and save them into the superset parquet using a GUI that runs on a bokeh server.

After connecting to [http://localhost:8000/database](http://localhost:8000/database) you should see the following app:


<img src="../images/database_widget.png" width="600" height="250" />

Select the your databse configuration and click connect to DB. If the connection is successful a the message will change to 
`Connected to db-url`, and the buttons on the parquet2sql file will be enabled.

You will need to load the following files, and save them to a new table in the database:

| **File name**                | **Table name**       |
|------------------------------|----------------------|
| developer_embeddings.parquet | developer_embeddings |
| commit_series.parquet        | commit_series        |
| metrics.parquet              | metrics              |

Click on the **parquet2sql** tab and use the file load to select the parquet files. The parquet files
are located in `dashboard_server/apps/load_data/data`.

<img src="../images/select_file.png" width="500" height="250" />

Once selected introduce the name of the table that will be created in the database and click **Write to DB**.

<img src="../images/write_new_table.png" width="400" height="250" />

The created table should be available right away in the **DB tables** drop down widget. You can visualize its contents
by selecting the table in the dropdown and clicking **Read DB table**.

<img src="../images/loaded_table.png" width="800" height="250" />

## Visualizing the graph of developer similarities

One of the apps running on the server allows to visualize the similarities among thevelopers
 using graphs. The represented chart has been constructed the following way:
 
- Each of our commit series will represent a node.
- Using the 2D embeddings for each commit series we connect each node to its 5 nearest neighbors
 in the embedding space.
- The weight of each edge in the graph is proportional to the distance to every other node.
- Each node is colored according to its hdbscan clustering.

You can access the plot in [http://localhost:8000/graph_plot](http://localhost:8000/graph_plot)
 as a separate enfpoint in the application, or through [http://localhost:5007/graph_plot](http://localhost:5007/graph_plot)
which is the bokeh server where the app is exposed.

| **Graph plot**               | **Interactive selection**|
|------------------------------|--------------------------|
| <img src="../images/similarities.png" width="350" height="350"/> | <img src="../images/interactive_graph.png" width="350" height="350"/>|

If you hover over the nodes, the information bout the series it represents will be displayed
. Also the nearest neighbours will be highlighted. It s also possible to click the nodes to make
 all the non-selected nodes fade.


