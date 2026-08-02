#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parallel, headless runner for the 8-method quantum-vs-classical FDS study.

It reuses the model / training code defined in
``notebooks/comparison/comprehensive_comparison.ipynb`` (single source of truth):
each worker process loads the notebook's setup + train-function cells into its own
namespace, then runs ONE (method, seed) job. Independent jobs are spread across CPU
cores with a process pool, so a high-core machine gets a near-linear speedup over the
sequential notebook runner.

Why processes (not joblib/threads in the notebook): PennyLane/TF objects and
notebook-defined closures are painful to pickle on Windows. Here nothing is pickled
except a method name (str) and a seed (int) -- each worker rebuilds everything locally.

Run it with the project's conda env, e.g.:
    C:\\ProgramData\\anaconda3\\envs\\my312\\python.exe src/run_experiments.py
    (the standalone Python312 has a broken TensorFlow -- see memory/runtime-environment)

Examples
--------
# Full study, all cores:
    python src/run_experiments.py
# Quick wiring check (cheap): 1 rep, 3 epochs, two methods, 2 workers:
    python src/run_experiments.py --reps 1 --epochs 3 --methods random_forest,qae_angle --n-jobs 2
# Quantum methods also at larger encoding dimensions (an1.11):
    python src/run_experiments.py --quantum-scaling 6,8
    python src/run_experiments.py --methods qae_angle,dife_qae --quantum-scaling config

Cost note for scaled runs: state-vector simulation is O(2^n) in device qubits, and
enhanced-qVAE doubles its data qubits via parallel embedding -- dim 4/6/8 means
13/17/21 device qubits there (vs 4/6/8 for QAE-Angle and DIFE). Measured at 1 epoch:
enhanced-qVAE takes ~20s at dim 4 but ~160s at dim 6. Keep --n-jobs low when a
high-dimension enhanced-qVAE job is in the pool; oversubscribing a small machine
made it die (the notebook's own try/except then reports "train function returned None").
"""
import os
os.environ.setdefault("MPLBACKEND", "Agg")          # headless: no GUI needed
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # quieten TensorFlow

import sys
import ast
import json
import time
import argparse
import contextlib
from concurrent.futures import ProcessPoolExecutor, as_completed

# the notebook's print() statements contain emoji; force UTF-8 so they never
# blow up on a Windows console / redirected stream using a legacy codepage.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(REPO, "notebooks", "comparison", "comprehensive_comparison.ipynb")
RESULTS_DIR = os.path.join(REPO, "results")

# method key -> train function name defined in the notebook.
# These are the notebook's SINGLE-run entry points (`_train_*_single`), never the
# `train_*` wrappers: a wrapper calls run_multiple_experiments() and would re-run
# n_repetitions trainings *inside* every job, so one 5-rep study would do 25
# trainings per method, ignore the per-job seed, and compute std over already
# averaged results. One job here == exactly one training (an1.14).
TRAIN_FN = {
    "random_forest":         "_train_rf_single",
    "isolation_forest":      "_train_if_single",
    "cnn_autoencoder":       "_train_cnn_single",
    "classical_autoencoder": "_train_ae_single",
    "qae_angle":             "_train_qae_angle_single",
    "enhanced_qvae":         "_train_enhanced_qvae_single",
    "dife_qae":              "_train_dife_qae_single",
    "ls_swap_qae":           "_train_ls_swap_qae_single",
    # H1 fairness: classical methods on the SAME PCA-4D space as the quantum methods
    "random_forest_4d":         "_train_rf_4d_single",
    "isolation_forest_4d":      "_train_if_4d_single",
    "classical_autoencoder_4d": "_train_ae_4d_single",
}
ALL_METHODS = list(TRAIN_FN)
# quantum methods that can be re-run at a larger encoding dimension (an1.11).
# Their scaled form is addressed with a "<method>@<dim>" key, e.g. "qae_angle@6",
# which the notebook resolves through quantum_scaled_single().
SCALABLE_METHODS = ["qae_angle", "enhanced_qvae", "dife_qae", "ls_swap_qae"]
# cells exec'd verbatim: imports / config / data / shared helpers
FULL_CELLS = [1, 2, 3, 4]
# cells holding train-function DEFINITIONS. Each ends with a top-level
# `xxx_result = train_xxx()` demo call that would run a FULL training at import
# time -- we strip everything except def/class/import so only the functions load.
DEF_CELLS = [6, 7, 8, 9, 11, 12, 13, 14, 19, 20]

# one cached notebook namespace per worker process (built lazily, reused across jobs)
_NS = None


def _defs_only(src):
    """Keep only function/class/import statements from a cell's source."""
    tree = ast.parse(src)
    tree.body = [n for n in tree.body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef, ast.Import, ast.ImportFrom))]
    return ast.unparse(tree)


def get_namespace():
    global _NS
    if _NS is None:
        # cell 3 reads ../../data/... relative to the notebook's own directory
        os.chdir(os.path.join(REPO, "notebooks", "comparison"))
        nb = json.load(open(NB, encoding="utf-8"))
        ns = {"__name__": "__main__"}
        with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull):
            for idx in FULL_CELLS:
                exec(compile("".join(nb["cells"][idx]["source"]), f"<nb cell {idx}>", "exec"), ns)
            for idx in DEF_CELLS:
                exec(compile(_defs_only("".join(nb["cells"][idx]["source"])),
                             f"<nb cell {idx} defs>", "exec"), ns)
        _NS = ns
    return _NS


def _apply_epochs_override(ns, epochs):
    if not epochs:
        return
    ns["EXPERIMENTAL_CONFIG"]["max_epochs"] = epochs
    qcfg = ns["QUANTUM_TRAINING_CONFIG"]
    for k in list(qcfg):
        if k.startswith("epochs_"):
            qcfg[k] = epochs


# keys kept from a train result. The full dicts also hold unpicklable objects
# (QNode 'circuit', qml 'dev', pnp 'weights', sklearn 'model', numpy arrays) which
# would crash the worker when it pickles its return value back to the orchestrator.
# 'n_qubits' is the DATA/encoding qubit count; enhanced-qVAE also reports
# 'total_qubits' (data + reference + trash + control), which is what the device
# actually allocates and therefore the resource figure the report needs.
_PASS_KEYS = ("method", "type", "n_qubits", "total_qubits")
_SCALAR_KEYS = ("auc", "accuracy", "precision", "recall", "f1_score",
                "gmean", "specificity", "threshold", "training_time")


def _sanitize(result):
    """Reduce a train result to picklable scalars needed for aggregation."""
    clean = {k: result[k] for k in _PASS_KEYS if k in result}
    for k in _SCALAR_KEYS:
        if result.get(k) is not None:
            try:
                clean[k] = float(result[k])
            except (TypeError, ValueError):
                pass
    return clean


def parse_method_key(method_key):
    """'qae_angle' -> ('qae_angle', None);  'qae_angle@6' -> ('qae_angle', 6)."""
    if "@" not in method_key:
        return method_key, None
    base, _, dim = method_key.partition("@")
    return base, int(dim)


def validate_method_key(method_key):
    """Return an error string if the key is unusable, else None."""
    base, dim = parse_method_key(method_key)
    if dim is None:
        return None if base in TRAIN_FN else f"unknown method key: {method_key!r}"
    if base not in SCALABLE_METHODS:
        return f"'{base}' cannot be scaled; scalable: {SCALABLE_METHODS}"
    if dim < 2:
        return f"encoding dimension must be >= 2, got {dim}"
    return None


def call_train(ns, method_key):
    """Run exactly one training for a (possibly dimension-scaled) method key."""
    base, dim = parse_method_key(method_key)
    if dim is None:
        return ns[TRAIN_FN[base]]()
    return ns["quantum_scaled_single"](base, dim)


def run_job(method_key, seed, rep_id, epochs=None):
    """Worker entry point: train one method once with a given seed."""
    ns = get_namespace()
    _apply_epochs_override(ns, epochs)
    ns["set_experiment_seed"](seed)
    t0 = time.time()
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull, contextlib.redirect_stdout(devnull):
            result = call_train(ns, method_key)
    except Exception as e:
        import traceback
        return {"method_key": method_key, "seed": seed, "rep_id": rep_id,
                "ok": False, "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc()}
    if result is None:
        return {"method_key": method_key, "seed": seed, "rep_id": rep_id,
                "ok": False, "error": "train function returned None"}
    result.setdefault("training_time", time.time() - t0)
    clean = _sanitize(result)              # drop unpicklable objects before returning
    clean["seed"] = seed
    clean["repetition_id"] = rep_id
    return {"method_key": method_key, "seed": seed, "rep_id": rep_id,
            "ok": True, "result": clean}


def _num(x):
    """float() but map non-finite (e.g. std with a single rep) to None for valid JSON."""
    import math
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def summarize(method_key, results, ns):
    """Build a clean mean/std summary for one method from its repetition results."""
    import numpy as np
    summ = ns["compute_statistical_summary_advanced"](results, method_key)
    clean = {
        "method": results[0].get("method", method_key),
        "type": results[0].get("type", ""),
        "n_qubits": results[0].get("n_qubits", 0),
        # device qubits: methods that allocate ancillas report it, others match n_qubits
        "total_qubits": results[0].get("total_qubits", results[0].get("n_qubits", 0)),
        "n_repetitions": len(results),
    }
    for metric in ["auc", "gmean", "f1_score", "precision", "recall", "accuracy", "specificity"]:
        if metric in summ:
            m = summ[metric]
            clean[metric] = {
                "mean": _num(m["mean"]), "std": _num(m["std"]),
                "min": _num(m["min"]), "max": _num(m["max"]),
                "ci_lower": _num(m.get("ci_lower", m["mean"])),
                "ci_upper": _num(m.get("ci_upper", m["mean"])),
            }
    tts = [float(r.get("training_time", 0.0)) for r in results]
    clean["training_time"] = {"mean": _num(np.mean(tts)),
                              "std": _num(np.std(tts, ddof=1)) if len(tts) > 1 else 0.0}
    return clean


def main():
    ap = argparse.ArgumentParser(description="Parallel runner for the 8-method FDS study.")
    ap.add_argument("--n-jobs", type=int, default=os.cpu_count(),
                    help="max concurrent worker processes (default: all CPU cores)")
    ap.add_argument("--reps", type=int, default=None,
                    help="repetitions per method (default: STATISTICAL_CONFIG.n_repetitions = 5)")
    ap.add_argument("--methods", type=str, default="all",
                    help="comma-separated method keys, or 'all'. Append '@<dim>' to re-run a "
                         "quantum method at a larger encoding dimension, e.g. 'qae_angle@6'. "
                         "Keys: " + ",".join(ALL_METHODS))
    ap.add_argument("--epochs", type=int, default=None,
                    help="override training epochs for ALL methods (for cheap validation runs)")
    ap.add_argument("--quantum-scaling", type=str, default=None, metavar="DIMS",
                    help="ALSO run every quantum method at these encoding dimensions "
                         "(comma-separated, e.g. '6,8'); 'config' uses the notebook's "
                         "QUANTUM_SCALING_CONFIG['pca_dimensions'] (an1.11)")
    args = ap.parse_args()

    methods = ALL_METHODS if args.methods == "all" else [m.strip() for m in args.methods.split(",")]

    # build the namespace once in the orchestrator (for seeds, config, aggregation utils)
    ns = get_namespace()

    if args.quantum_scaling:
        dims = (ns["QUANTUM_SCALING_CONFIG"]["pca_dimensions"] if args.quantum_scaling == "config"
                else [int(d) for d in args.quantum_scaling.split(",")])
        methods += [f"{m}@{d}" for d in dims for m in SCALABLE_METHODS if m in methods]

    bad = [(m, err) for m in methods if (err := validate_method_key(m))]
    if bad:
        ap.error("; ".join(f"{m}: {err}" for m, err in bad))

    n_reps = args.reps if args.reps is not None else ns["STATISTICAL_CONFIG"]["n_repetitions"]
    seeds = ns["experiment_seeds"][:n_reps]

    jobs = [(mk, seeds[i], i + 1) for mk in methods for i in range(n_reps)]
    n_jobs = max(1, min(args.n_jobs, len(jobs)))

    print("=" * 78)
    print(" PARALLEL EXPERIMENT RUN")
    print("=" * 78)
    print(f"  methods    : {len(methods)}  -> {methods}")
    print(f"  reps/method: {n_reps}   seeds: {seeds}")
    print(f"  total jobs : {len(jobs)}   workers: {n_jobs}   cpu cores: {os.cpu_count()}")
    if args.epochs:
        print(f"  epochs     : OVERRIDDEN to {args.epochs} (validation mode)")
    print("=" * 78, flush=True)

    grouped = {mk: [] for mk in methods}
    failures = []
    t_start = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=n_jobs) as ex:
        futs = {ex.submit(run_job, mk, s, rid, args.epochs): (mk, s, rid) for mk, s, rid in jobs}
        for fut in as_completed(futs):
            mk, s, rid = futs[fut]
            done += 1
            rec = fut.result()
            elapsed = time.time() - t_start
            if rec["ok"]:
                r = rec["result"]
                grouped[mk].append(r)
                print(f"  [{done:>2}/{len(jobs)}] {elapsed:6.0f}s  OK  {mk:<22} "
                      f"rep{rid} seed={s}  G-Mean={r.get('gmean', 0):.4f}  "
                      f"({r.get('training_time', 0):.0f}s)", flush=True)
            else:
                failures.append(rec)
                print(f"  [{done:>2}/{len(jobs)}] {elapsed:6.0f}s  FAIL {mk:<22} "
                      f"rep{rid} seed={s}  {rec['error']}", flush=True)

    # aggregate
    final = {}
    for mk in methods:
        if grouped[mk]:
            final[mk] = summarize(mk, grouped[mk], ns)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(RESULTS_DIR, f"experiment_results_parallel_{ts}.json")
    payload = {
        "config": {"methods": methods, "n_repetitions": n_reps, "seeds": seeds,
                   "n_jobs": n_jobs, "epochs_override": args.epochs,
                   "wall_clock_seconds": round(time.time() - t_start, 1)},
        "summary": final,
        "failures": [{k: v for k, v in f.items() if k != "traceback"} for f in failures],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # final table
    print("\n" + "=" * 78)
    print(" RESULTS (mean +/- std over repetitions)")
    print("=" * 78)
    def ms(d):  # "mean+/-std" with None-safe formatting (std is None for a single rep)
        mean, std = d.get("mean"), d.get("std")
        mean_s = f"{mean:.4f}" if mean is not None else " n/a "
        std_s = f"{std:.4f}" if std is not None else "n/a"
        return f"{mean_s}+/-{std_s}"

    print(f"  {'method':<22} {'type':<14} {'G-Mean':>16} {'AUC':>16} {'data q':>7} {'dev q':>6}")
    for mk in methods:
        c = final.get(mk)
        if not c:
            print(f"  {mk:<22} {'(no results)':<14}")
            continue
        print(f"  {c['method']:<22} {c['type']:<14} "
              f"{ms(c.get('gmean', {})):>16} {ms(c.get('auc', {})):>16} "
              f"{c['n_qubits']:>7} {c['total_qubits']:>6}")
    print("=" * 78)
    print(f"  wall-clock: {time.time() - t_start:.0f}s   failures: {len(failures)}")
    print(f"  saved: {out_path}")
    if failures:
        print("  NOTE: some jobs failed; see the failures list above / in the JSON.")


if __name__ == "__main__":
    main()
