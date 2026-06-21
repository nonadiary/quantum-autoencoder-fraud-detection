# Running the full study on a rented CPU box

The full study (8 methods × 5 repetitions × 100 epochs) is too slow on a 2-core
laptop. Rent a **high-core CPU** instance, run it there in ~tens of minutes, copy
the results back, and delete the box. Total cost is roughly **$1–2**.

> **Why CPU, not GPU?** At 4–13 qubits the quantum state vectors are tiny, so a GPU
> gives no speedup (often slower). The win comes from running the independent
> (method, seed) jobs across many CPU cores — that's what `src/run_experiments.py` does.

---

## 1. Rent a box

- **Recommended:** [Hetzner Cloud](https://console.hetzner.cloud) → new server →
  **CCX43** (16 dedicated AMD vCPU, 64 GB) → image **Ubuntu 24.04**. Billed hourly;
  you'll only need it for ~1 hour. (CCX33 / 8 vCPU is a cheaper, slightly slower option.)
- Any equivalent works (AWS `c7a.4xlarge`/`c7a.8xlarge` in Seoul `ap-northeast-2`, GCP `c3-highcpu`, …).
- Add your SSH key when creating the server, then connect:
  ```bash
  ssh root@<BOX_IP>
  ```

## 2. Get the code onto the box

**Option A — git (recommended).** First push your local commits from this machine:
```bash
git push origin main
```
Then on the box:
```bash
git clone https://github.com/nonadiary/quantum-autoencoder-fraud-detection.git
cd quantum-autoencoder-fraud-detection
```

**Option B — copy directly** (no push needed), run from your laptop:
```bash
scp -r "c:/GitHub/quantum-autoencoder-fraud-detection" root@<BOX_IP>:~/qae
# then on the box:  cd ~/qae
```
The balanced dataset (`data/preprocessed-creditcard.csv`, ~0.5 MB) is included in the
repo, so you do **not** need the 144 MB raw `creditcard.csv`.

## 3. Install dependencies

```bash
bash scripts/setup_remote.sh
```
This creates a `.venv`, installs the pinned stack (`requirements-run.txt`), and prints
a sanity check. Takes a few minutes (TensorFlow + PennyLane are large).

## 4. Run the study

Use `tmux` (or `nohup`) so the run survives an SSH disconnect:
```bash
. .venv/bin/activate
nohup python src/run_experiments.py > run.log 2>&1 &
tail -f run.log        # watch progress; Ctrl-C just stops watching, not the run
```
Defaults: all 8 methods, 5 repetitions, `--n-jobs` = all cores. Useful flags:
- `--n-jobs 16` — cap concurrent workers (default already = core count)
- `--reps 5` — repetitions per method
- `--methods qae_angle,enhanced_qvae` — subset
- `--epochs 3` — **cheap validation** run before committing to the full one

Expected wall-clock on 16 vCPU: roughly **30–60 minutes** (vs many hours sequentially).

## 5. Get the results back

The runner writes `results/experiment_results_parallel_<timestamp>.json`. Copy it to
your laptop:
```bash
scp root@<BOX_IP>:~/quantum-autoencoder-fraud-detection/results/experiment_results_parallel_*.json \
    "c:/GitHub/quantum-autoencoder-fraud-detection/results/"
```

## 6. Delete the box (stop billing!)

In the Hetzner console, **delete** the server (don't just power off — powered-off
servers still bill). Then back on your laptop, the JSON's mean ± std numbers feed the
README / report update (beads `an1.4`).

---

### Sanity-check first (optional, ~1 min)
Before the full run, confirm everything works cheaply:
```bash
python src/run_experiments.py --reps 1 --epochs 3 --methods random_forest,qae_angle --n-jobs 2
```
Both jobs should report `OK` and a results JSON should be written.
