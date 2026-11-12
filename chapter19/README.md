# Chapter 19 — Traffic Prediction - Using Graph Neural Networks (GNN) on Road Networks

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `stgcn_for_simulated_traffic_forecasting/example/` | `01_stgcn_forward.py` | Generates a four-by-four city grid with NetworkX, turns its adjacency into the normalized operator a graph convolution consumes, and runs one STGCN block over twelve time steps of speed and volume. |
| `road_network_graph_initialization/example/` | `01_road_network_graph.py` | Turns six road segments and fifteen sensor readings into the two inputs a graph neural network needs: a 5x5 adjacency matrix that says which intersections touch, and a (nodes, time, features) tensor that says how fast the traffic was. |
| `exercise_1_gis_data_transformation_and_graph/exercise/` | `01_graph_construction.py` | Takes the two datasets the exercise describes — a road network and a week of sensor readings — and produces the four artefacts an STGCN expects: a symmetric adjacency matrix, its normalized Laplacian with self-loops, a feature tensor of shape (time, nodes, features) with a clock encoded in it, and sliding windows that never let a future step into the past. |
| `exercise_2_implementing_the_spatio_temporal_c/exercise/` | `01_stconv_block.py` | Builds one ST-Conv block in PyTorch: a gated temporal convolution, a spatial convolution in the Chebyshev basis of the scaled Laplacian, and a second gated temporal convolution, with a residual path that reslices the shortened time axis. |
| `exercise_3_model_training_hyperparameter_opti/exercise/` | `01_train_stgcn.py` | Assembles two ST-Conv blocks and a per-node head, runs the grid the exercise asks for (Chebyshev order, temporal kernel, hidden width), keeps the combination with the lowest validation error, retrains it and reports MAE, RMSE and R^2 on the held-out tail of the day — overall and for each of the three horizons separately. |
| `exercise_4_interactive_challenge_asynchronous/exercise/` | `01_async_stream.py` | Consumes a simulated live traffic feed with `async with` and `async for`, predicts on each batch, and renders the result while the stream is idle. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter19/run_offline.sh
```

`run_offline.sh` runs the 6 harnesses and prints one line per harness;
the log is written to `chapter19/output/run_19.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
