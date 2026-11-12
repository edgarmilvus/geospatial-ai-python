"""Harness for chapter 19, example 1 — the two GNN inputs, checked by domain facts.

The point of the example is arithmetic anyone can confirm by hand: six undirected
road segments give twelve ones in a 5x5 matrix, B touches three of the four other
intersections, and the normalization puts 1/(degree+1) on the diagonal. Those are
the assertions; the string checks on what it prints come last.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 1 (road network graph)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_road_network_graph.py", "road_network_graph")
    printed = log.getvalue()

    A = module.A
    X = module.X
    an = module.A_norm

    # --- the topology ---
    h.equal(A.shape, (5, 5), "A is square, one row and column per intersection")
    h.equal(int(A.sum()), 12, "six undirected roads put twelve ones in A")
    h.check(bool((A == A.T).all()), "A is symmetric: every road is two-way")
    h.equal(int(A.diagonal().sum()), 0, "the base matrix has no self-loops")
    h.equal(sorted(A.sum(axis=1).tolist()), [2, 2, 2, 3, 3],
            "degrees are 2,2,2,3,3: B and D carry the bypass")
    h.equal(int(A[1].sum()), 3, "intersection B has three neighbours")
    h.equal([i for i in range(5) if A[1, i]], [0, 2, 3],
            "B is joined to A, C and D, exactly as the edge list says")

    # --- the tensor ---
    h.equal(X.shape, (5, 3, 2), "X is (nodes, timesteps, features)")
    h.equal(float(X[0, 0, 0]), 55.0, "A's most recent speed survives the reshape")
    h.equal(X[1, :, 1].tolist(), [25.0, 20.0, 18.0],
            "B's volume history is 25, 20, 18 vehicles per minute")
    h.equal(float(X[2, 0, 0]), 65.0, "C is the fastest segment at T=0")

    # --- the operator the pitfall builds ---
    h.equal(an.shape, (5, 5), "the normalized operator is the same size as A")
    h.check(bool(abs(an - an.T).max() < 1e-12), "A_norm is symmetric")
    degrees = A.sum(axis=1) + 1
    h.check(bool(abs(an.diagonal() - 1.0 / degrees).max() < 1e-12),
            "the diagonal of A_norm is 1/(degree+1): the self-loop weight")
    h.close(float(an.trace()), 1.5, "trace(A_norm) is 1/3+1/4+1/3+1/4+1/3")
    h.close(float(an[0, 1]), 1 / (3 * 4) ** 0.5,
            "the A-B entry is 1/sqrt(3*4), the degree-normalized weight")

    # --- what the reader sees ---
    h.contains(printed, "Degree (number of neighbours): 3", "the run reports B's degree")
    h.contains(printed, "['Intersection_A', 'Intersection_C', 'Intersection_D']",
               "the run names B's neighbours")
    h.contains(printed, "Symmetric: True", "the run confirms the matrix is undirected")
    h.contains(printed, "Trace of A_norm: 1.5000", "the run prints the normalization check")

    artefact = json.loads((FILES.parent / "output" / "road_network_graph.json").read_text())
    h.equal(artefact["degree_total"], 12, "the artefact records the degree sum")
    h.equal(artefact["feature_shape"], [5, 3, 2], "the artefact records the tensor shape")

    h.write_json("road_network_example.json", {
        "nodes": len(module.NODES),
        "edges": len(module.ROAD_CONNECTIONS),
        "adjacency_shape": list(A.shape),
        "degree_sum": int(A.sum()),
        "degrees": A.sum(axis=1).tolist(),
        "feature_shape": list(X.shape),
        "trace_a_norm": round(float(an.trace()), 6),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (road network graph)", FILES).crash())
