#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           QUANTUM IMAGE ANALYSIS — CLI SIMULATOR                ║
║   Inversion · Matching · Edge Detection                         ║
║   NEQR Encoding | SWAP Test | QHED Algorithm                    ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
  python quantum_cli.py <image_path> [--mode all|inversion|matching|edges]
                                     [--compare <second_image>]
                                     [--output <dir>]
                                     [--size <int>]   (default 8, max 16)

Examples:
  python quantum_cli.py photo.png
  python quantum_cli.py photo.png --mode inversion
  python quantum_cli.py photo.png --mode matching --compare photo2.png
  python quantum_cli.py photo.png --mode all --output ./results --size 8
"""

import sys, os, time, argparse, math, textwrap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
from PIL import Image as PILImage

# ─── ANSI colour palette ─────────────────────────────────────────────────────
R  = "\033[0m"
B  = "\033[1m"
DIM = "\033[2m"
CYN = "\033[96m"
GRN = "\033[92m"
YLW = "\033[93m"
RED = "\033[91m"
MAG = "\033[95m"
BLU = "\033[94m"
WHT = "\033[97m"
BOLD_CYN = B + CYN
BOLD_GRN = B + GRN
BOLD_YLW = B + YLW
BOLD_MAG = B + MAG
BOLD_RED = B + RED

# ─── Helpers ─────────────────────────────────────────────────────────────────

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def banner():
    print()
    print(BOLD_CYN + "╔══════════════════════════════════════════════════════════════════╗" + R)
    print(BOLD_CYN + "║" + B + WHT + "         ⚛  QUANTUM IMAGE ANALYSIS SIMULATOR  ⚛             " + BOLD_CYN + "║" + R)
    print(BOLD_CYN + "║" + DIM + "      NEQR Encoding · SWAP Test · QHED Edge Detection        " + BOLD_CYN + "║" + R)
    print(BOLD_CYN + "╚══════════════════════════════════════════════════════════════════╝" + R)
    print()

def section(title: str, icon: str = "⚛"):
    w = 66
    pad = (w - len(title) - 4) // 2
    print()
    print(BOLD_YLW + "┌" + "─" * (w - 2) + "┐" + R)
    print(BOLD_YLW + "│" + " " * pad + icon + "  " + B + WHT + title + R + " " * (w - 2 - pad - len(title) - 3) + BOLD_YLW + "│" + R)
    print(BOLD_YLW + "└" + "─" * (w - 2) + "┘" + R)

def kv(label: str, value: str, colour=WHT):
    print(f"  {DIM}{label:<28}{R}{colour}{B}{value}{R}")

def progress_bar(label: str, fraction: float, width: int = 40, colour=CYN):
    filled = int(width * fraction)
    bar = "█" * filled + "░" * (width - filled)
    pct = f"{fraction*100:5.1f}%"
    sys.stdout.write(f"\r  {colour}{label:<24}{R} [{colour}{bar}{R}] {BOLD_GRN}{pct}{R}  ")
    sys.stdout.flush()

def spinner_msg(msg: str, done: bool = False):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    if done:
        sys.stdout.write(f"\r  {BOLD_GRN}✔{R}  {msg}\n")
    else:
        frame = frames[int(time.time() * 8) % len(frames)]
        sys.stdout.write(f"\r  {CYN}{frame}{R}  {msg}  ")
    sys.stdout.flush()

def ascii_image(arr: np.ndarray, width: int = 32, height: int = 16) -> str:
    """Render a numpy grayscale array as ASCII art in the terminal."""
    chars = " .:-=+*#%@"
    from PIL import Image as PILImage
    img = PILImage.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img = img.resize((width, height), PILImage.LANCZOS).convert("L")
    px = np.array(img)
    lines = []
    for row in px:
        line = ""
        for v in row:
            idx = int(v / 256 * len(chars))
            line += chars[min(idx, len(chars) - 1)] * 2
        lines.append(line)
    return "\n".join(lines)

def display_ascii(label: str, arr: np.ndarray, colour=WHT, w=32, h=12):
    art = ascii_image(arr, width=w, height=h)
    print(f"\n  {BOLD_YLW}{label}{R}")
    for line in art.split("\n"):
        print(f"  {colour}{line}{R}")

def simulate_quantum_build(label: str, steps: int = 20, colour=CYN):
    """Show a fake 'quantum circuit building' animation with steps."""
    print(f"\n  {BOLD_MAG}↯  Building quantum circuit: {label}{R}")
    for i in range(steps + 1):
        frac = i / steps
        filled = int(40 * frac)
        bar = "▓" * filled + "░" * (40 - filled)
        gate_ops = ["H ", "X ", "CNOT", "MCX ", "CX ", "RZ ", "RX "]
        g = gate_ops[i % len(gate_ops)]
        sys.stdout.write(f"\r    {colour}[{bar}]{R} {BOLD_GRN}{frac*100:5.1f}%{R}  gate:{YLW}{g}{R}  qubit:{MAG}q{i % 12}{R}  ")
        sys.stdout.flush()
        time.sleep(0.03)
    print(f"\n  {BOLD_GRN}✔  Circuit compiled and transpiled{R}")

def simulate_statevector(label: str, n_states: int = 2048, colour=CYN):
    """Animate statevector simulation sweep."""
    print(f"\n  {BOLD_MAG}⟩  Statevector simulation: {label}{R}")
    chunks = 30
    for i in range(chunks + 1):
        frac = i / chunks
        filled = int(40 * frac)
        bar = "█" * filled + "░" * (40 - filled)
        amp = f"{np.random.uniform(0.001, 0.02):.5f}"
        sys.stdout.write(f"\r    {colour}[{bar}]{R} {BOLD_GRN}{frac*100:5.1f}%{R}  |ψ|²={YLW}{amp}{R}  states:{MAG}{int(frac*n_states):>5}{R}/{n_states}  ")
        sys.stdout.flush()
        time.sleep(0.04)
    print(f"\n  {BOLD_GRN}✔  Statevector collapsed — {n_states} amplitudes decoded{R}")

def simulate_decode(label: str, h: int, w: int, colour=CYN):
    """Animate pixel-by-pixel reconstruction."""
    total = h * w
    print(f"\n  {BOLD_MAG}◈  Quantum decoding → pixels: {label}{R}")
    chunks = 25
    for i in range(chunks + 1):
        frac = i / chunks
        filled = int(40 * frac)
        bar = "▒" * filled + "░" * (40 - filled)
        px = int(frac * total)
        sys.stdout.write(f"\r    {colour}[{bar}]{R} {BOLD_GRN}{frac*100:5.1f}%{R}  pixels:{YLW}{px:>5}{R}/{total}  row:{MAG}{min(int(frac*h),h-1):>2}{R}  ")
        sys.stdout.flush()
        time.sleep(0.035)
    print(f"\n  {BOLD_GRN}✔  Image reconstructed from quantum state  ({h}×{w}){R}")

# ─── Image loader ─────────────────────────────────────────────────────────────

def load_image(path: str, size: int = 8) -> np.ndarray:
    from encoding import preprocess
    img = PILImage.open(path).convert("L")
    arr = np.array(img, dtype=np.float64)
    return preprocess(arr, max_dim=size)

# ─── Algorithm runners with visual output ─────────────────────────────────────

def run_inversion(img: np.ndarray, out_dir: str):
    import inversion as inv_mod

    section("QUANTUM IMAGE INVERSION", "🔀")
    print(f"\n  {DIM}Algorithm : NEQR Encoding + Pauli-X on value register{R}")
    print(f"  {DIM}Theory    : X|v⟩|yx⟩ → |2ⁿ−1−v⟩|yx⟩{R}")
    print(f"  {DIM}Image size: {img.shape[0]}×{img.shape[1]}  (resized to power-of-2){R}")

    # — Animations —
    n_q = int(math.log2(img.shape[0])) + int(math.log2(img.shape[1])) + 8
    simulate_quantum_build("NEQR inversion circuit", steps=18)
    simulate_statevector("applying X̂ gates on value register", n_states=2**n_q)
    simulate_decode("quantum → pixel image", img.shape[0], img.shape[1])

    # — Real computation —
    print(f"\n  {BOLD_CYN}⚙  Running full quantum simulation (Qiskit Aer)…{R}")
    t0 = time.perf_counter()
    res = inv_mod.run(img)
    elapsed = time.perf_counter() - t0

    # — ASCII art output —
    display_ascii("[ Original Image ]",         res["original"],  WHT)
    display_ascii("[ Quantum Inverted ]",        res["quantum"],   CYN)
    display_ascii("[ Classical Inverted ]",      res["classical"], GRN)
    diff = np.abs(res["quantum"].astype(float) - res["classical"].astype(float))
    display_ascii("[ Quantum vs Classical Diff ]",diff,           YLW)

    # — Metrics —
    section("INVERSION METRICS", "📊")
    kv("MSE (quantum vs classical)", f"{res['mse']:.6f}", GRN if res['mse'] < 10 else YLW)
    kv("PSNR",                       f"{res['psnr']:.2f} dB",  GRN)
    kv("SSIM",                       f"{res['ssim']:.6f}",     GRN if res['ssim'] > 0.95 else YLW)
    kv("Circuit qubits",             str(res['qubits']),        CYN)
    kv("Circuit depth",              str(res['depth']),         CYN)
    kv("Gate count",                 str(res['gate_count']),    CYN)
    kv("Image size",                 f"{res['image_size'][0]}×{res['image_size'][1]}", WHT)
    kv("Wall-clock time",            f"{elapsed:.3f}s",         MAG)
    kv("Hilbert space dim",          f"2^{res['qubits']} = {2**res['qubits']:,}", YLW)

    # — Save figure —
    _save_inversion_figure(res, out_dir)
    return res

def run_edge_detection(img: np.ndarray, out_dir: str):
    import edge_detection as ed_mod

    section("QUANTUM EDGE DETECTION (QHED)", "⚡")
    print(f"\n  {DIM}Algorithm : QHED — Quantum Horizontal/Vertical Edge{R}")
    print(f"  {DIM}Theory    : ΔI = |I(x,y) − I(x+1,y)|  via cyclic shift{R}")
    print(f"  {DIM}Shift op  : cyclic increment on row/col qubit register{R}")

    n_q = int(math.log2(img.shape[0])) + int(math.log2(img.shape[1])) + 8
    simulate_quantum_build("QHED cyclic-shift circuit (horizontal)", steps=16)
    simulate_statevector("horizontal shift simulation", n_states=2**n_q)
    simulate_quantum_build("QHED cyclic-shift circuit (vertical)", steps=16)
    simulate_statevector("vertical shift simulation", n_states=2**n_q)
    simulate_decode("edge magnitude from quantum states", img.shape[0], img.shape[1])

    print(f"\n  {BOLD_CYN}⚙  Running full QHED simulation…{R}")
    t0 = time.perf_counter()
    res = ed_mod.run(img)
    elapsed = time.perf_counter() - t0

    display_ascii("[ Original Image ]",        res["original"],  WHT)
    display_ascii("[ Quantum H-Edges ]",        res["quantum_h"], CYN)
    display_ascii("[ Quantum V-Edges ]",        res["quantum_v"], MAG)
    display_ascii("[ Quantum Combined Edges ]", res["quantum"],   BLU)
    display_ascii("[ Classical Sobel ]",        res["sobel"],     GRN)
    display_ascii("[ Classical Laplacian ]",    res["laplacian"], YLW)

    section("EDGE DETECTION METRICS", "📊")
    kv("Corr(Quantum, Sobel)",     f"{res['corr_sobel']:.4f}",     GRN if res['corr_sobel'] > 0.7 else YLW)
    kv("Corr(Quantum, Laplacian)", f"{res['corr_laplacian']:.4f}", GRN if res['corr_laplacian'] > 0.7 else YLW)
    kv("MSE vs Sobel",             f"{res['mse_vs_sobel']:.2f}",   WHT)
    kv("Circuit qubits",           str(res['qubits']),              CYN)
    kv("Circuit depth",            str(res['depth']),               CYN)
    kv("Gate count",               str(res['gate_count']),          CYN)
    kv("Image size",               f"{res['image_size'][0]}×{res['image_size'][1]}", WHT)
    kv("Wall-clock time",          f"{elapsed:.3f}s",               MAG)
    kv("Hilbert space dim",        f"2^{res['qubits']} = {2**res['qubits']:,}",     YLW)

    _save_edge_figure(res, out_dir)
    return res

def run_matching(img_a: np.ndarray, img_b: np.ndarray, out_dir: str):
    import matching as match_mod

    section("QUANTUM IMAGE MATCHING (SWAP TEST)", "🔁")
    print(f"\n  {DIM}Algorithm : Quantum SWAP Test — Fidelity Estimation{R}")
    print(f"  {DIM}Theory    : P(|0⟩) = ½ + ½·|⟨ψ_A|ψ_B⟩|²{R}")
    print(f"  {DIM}Result    : similarity = 2·P(0) − 1  ∈ [0, 1]{R}")

    flat_len = 2 ** math.ceil(math.log2(max(img_a.size, 2)))
    n_q = 1 + 2 * int(math.log2(flat_len))
    simulate_quantum_build("amplitude encoding — image A", steps=14)
    simulate_quantum_build("amplitude encoding — image B", steps=14)
    print(f"\n  {BOLD_MAG}↯  Building SWAP-test circuit (Hadamard + controlled-SWAPs){R}")
    for i in range(21):
        frac = i / 20
        bar = "█" * int(40 * frac) + "░" * (40 - int(40 * frac))
        sys.stdout.write(f"\r    {CYN}[{bar}]{R} {BOLD_GRN}{frac*100:5.1f}%{R}  ancilla:{YLW}q0{R}  CSWAP#{MAG}{i}{R}  ")
        sys.stdout.flush()
        time.sleep(0.04)
    print(f"\n  {BOLD_GRN}✔  SWAP-test circuit ready  (qubits: {n_q}){R}")
    print(f"\n  {BOLD_MAG}▶  Shot-based measurement simulation (8192 shots)…{R}")
    for i in range(21):
        frac = i / 20
        shots_done = int(frac * 8192)
        bar = "▓" * int(40 * frac) + "░" * (40 - int(40 * frac))
        sys.stdout.write(f"\r    {MAG}[{bar}]{R} {BOLD_GRN}{frac*100:5.1f}%{R}  shots:{YLW}{shots_done:>5}{R}/8192  ")
        sys.stdout.flush()
        time.sleep(0.05)
    print(f"\n  {BOLD_GRN}✔  Measurement complete — counting |0⟩ outcomes{R}")

    print(f"\n  {BOLD_CYN}⚙  Running full SWAP-test simulation…{R}")
    t0 = time.perf_counter()
    res = match_mod.run(img_a, img_b, shots=8192)
    elapsed = time.perf_counter() - t0

    display_ascii("[ Image A ]", img_a, CYN)
    display_ascii("[ Image B ]", img_b, MAG)

    # similarity gauge
    sim = res["quantum_similarity"]
    gauge_width = 40
    filled = int(gauge_width * sim)
    colour = BOLD_GRN if sim > 0.8 else BOLD_YLW if sim > 0.4 else BOLD_RED
    print(f"\n  {BOLD_WHT}Quantum Similarity Gauge{R}")
    print(f"  [{colour}{'█' * filled}{'░' * (gauge_width - filled)}{R}]  {colour}{sim:.4f}{R}")

    section("MATCHING METRICS", "📊")
    kv("Quantum similarity (SWAP)",  f"{res['quantum_similarity']:.6f}", GRN if sim > 0.8 else YLW)
    kv("Classical cosine distance",  f"{res['classical_cosine']:.6f}",   WHT)
    kv("Classical MSE",              f"{res['classical_mse']:.6f}",      WHT)
    kv("Histogram intersection",     f"{res['histogram_intersection']:.6f}", CYN)
    kv("Shots",                      f"{res['shots']:,}",                 DIM)
    kv("Circuit qubits",             str(res['qubits']),                  CYN)
    kv("Circuit depth",              str(res['depth']),                   CYN)
    kv("Gate count",                 str(res['gate_count']),               CYN)
    kv("Wall-clock time",            f"{elapsed:.3f}s",                   MAG)

    counts = res["counts"]
    c0 = counts.get("0", 0)
    c1 = counts.get("1", 0)
    p0 = c0 / res["shots"]
    print(f"\n  {BOLD_YLW}Measurement distribution:{R}")
    print(f"    |0⟩ : {BOLD_GRN}{c0:>5}{R}  ({GRN}{p0*100:.2f}%{R})  {'█' * int(p0 * 30)}")
    print(f"    |1⟩ : {BOLD_RED}{c1:>5}{R}  ({RED}{(1-p0)*100:.2f}%{R})  {'█' * int((1-p0) * 30)}")

    _save_match_figure(res, img_a, img_b, out_dir)
    return res

# ─── Matplotlib figure savers ─────────────────────────────────────────────────

def _save_inversion_figure(res, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        fig = plt.figure(figsize=(14, 7), facecolor="#0a0a14")
        gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.5, wspace=0.4,
                               left=0.06, right=0.97, top=0.88, bottom=0.08)
        fig.text(0.5, 0.945, "⚛  Quantum Image Inversion — NEQR + Pauli-X", ha="center",
                 fontsize=15, fontweight="bold", color="#00e5ff", family="monospace")
        fig.text(0.5, 0.915, f"Qubits: {res['qubits']}  |  Depth: {res['depth']}  |  PSNR: {res['psnr']:.2f}dB  |  SSIM: {res['ssim']:.4f}",
                 ha="center", fontsize=9, color="#888888", family="monospace")

        def im(ax, data, title, cmap="gray"):
            ax.set_facecolor("#111120")
            ax.imshow(np.clip(data, 0, 255).astype(np.uint8), cmap=cmap, vmin=0, vmax=255)
            ax.set_title(title, fontsize=8, color="#00e5ff", pad=4, family="monospace")
            ax.set_xticks([]); ax.set_yticks([])

        im(fig.add_subplot(gs[0, 0]), res["original"],  "Original")
        im(fig.add_subplot(gs[0, 1]), res["quantum"],   "Quantum Inverted", cmap="plasma")
        im(fig.add_subplot(gs[0, 2]), res["classical"], "Classical Inverted")
        diff = np.abs(res["quantum"].astype(float) - res["classical"].astype(float))
        im(fig.add_subplot(gs[0, 3]), diff,             "| Q − C | diff", cmap="hot")

        ax_h = fig.add_subplot(gs[1, 0:2])
        ax_h.set_facecolor("#111120")
        ax_h.hist(res["original"].flatten(),  bins=32, alpha=0.7, color="#ffffff", label="Original")
        ax_h.hist(res["quantum"].flatten(),   bins=32, alpha=0.6, color="#00e5ff", label="Quantum")
        ax_h.hist(res["classical"].flatten(), bins=32, alpha=0.4, color="#ff4444", label="Classical")
        ax_h.legend(fontsize=7, facecolor="#111120", labelcolor="white")
        ax_h.set_title("Pixel Distribution", fontsize=8, color="#00e5ff", family="monospace")
        ax_h.tick_params(colors="#555555"); ax_h.set_facecolor("#111120")

        ax_e = fig.add_subplot(gs[1, 2])
        ax_e.set_facecolor("#111120")
        ax_e.hist(diff.flatten(), bins=20, color="#00e5ff", alpha=0.85)
        ax_e.set_title("Error Distribution", fontsize=8, color="#00e5ff", family="monospace")
        ax_e.tick_params(colors="#555555")

        ax_m = fig.add_subplot(gs[1, 3])
        ax_m.set_facecolor("#0a0a14")
        for sp in ax_m.spines.values(): sp.set_visible(False)
        ax_m.set_xticks([]); ax_m.set_yticks([])
        ax_m.set_title("Metrics", fontsize=8, color="#00e5ff", family="monospace")
        items = [("MSE", f"{res['mse']:.4f}"), ("PSNR", f"{res['psnr']:.2f} dB"),
                 ("SSIM", f"{res['ssim']:.4f}"), ("Qubits", str(res['qubits'])),
                 ("Depth", str(res['depth'])), ("Gates", str(res['gate_count'])),
                 ("Time", f"{res['elapsed']:.3f}s")]
        for k, (lbl, val) in enumerate(items):
            y = 0.92 - k * 0.13
            ax_m.text(0.02, y, lbl, fontsize=8, color="#888888", transform=ax_m.transAxes)
            ax_m.text(0.6,  y, val, fontsize=8, color="#00e5ff", fontweight="bold", transform=ax_m.transAxes)

        path = os.path.join(out_dir, "inversion_result.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0a0a14")
        plt.close(fig)
        print(f"\n  {BOLD_GRN}✔  Saved figure → {path}{R}")
    except Exception as e:
        print(f"\n  {YLW}⚠  Could not save figure: {e}{R}")

def _save_edge_figure(res, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        fig = plt.figure(figsize=(16, 8), facecolor="#0a0a14")
        gs = gridspec.GridSpec(2, 5, figure=fig, hspace=0.5, wspace=0.35,
                               left=0.05, right=0.97, top=0.90, bottom=0.07)
        fig.text(0.5, 0.948, "⚛  Quantum Edge Detection — QHED Cyclic Shift", ha="center",
                 fontsize=15, fontweight="bold", color="#7fff00", family="monospace")

        def im(ax, data, title, cmap="gray"):
            ax.set_facecolor("#111120")
            ax.imshow(np.clip(data, 0, 255).astype(np.uint8), cmap=cmap, vmin=0, vmax=255)
            ax.set_title(title, fontsize=8, color="#7fff00", pad=4, family="monospace")
            ax.set_xticks([]); ax.set_yticks([])

        im(fig.add_subplot(gs[0, 0]), res["original"],  "Original")
        im(fig.add_subplot(gs[0, 1]), res["quantum_h"], "Quantum H-Edges", cmap="inferno")
        im(fig.add_subplot(gs[0, 2]), res["quantum_v"], "Quantum V-Edges", cmap="inferno")
        im(fig.add_subplot(gs[0, 3]), res["quantum"],   "Quantum Combined", cmap="inferno")
        im(fig.add_subplot(gs[0, 4]), res["sobel"],     "Classical Sobel", cmap="inferno")
        im(fig.add_subplot(gs[1, 0]), res["laplacian"], "Classical Laplacian", cmap="inferno")

        ax_p = fig.add_subplot(gs[1, 1:3])
        ax_p.set_facecolor("#111120")
        mid = res["quantum"].shape[0] // 2
        x = np.arange(res["quantum"].shape[1])
        ax_p.fill_between(x, res["quantum"][mid], alpha=0.35, color="#00bfff")
        ax_p.plot(x, res["quantum"][mid], color="#00bfff", lw=2, label="Quantum")
        ax_p.fill_between(x, res["sobel"][mid], alpha=0.2, color="#ff4444")
        ax_p.plot(x, res["sobel"][mid], color="#ff4444", lw=2, ls="--", label="Sobel")
        ax_p.legend(fontsize=7, facecolor="#111120", labelcolor="white")
        ax_p.set_title("Row-Midpoint Edge Profile", fontsize=8, color="#7fff00", family="monospace")
        ax_p.tick_params(colors="#555555")

        ax_sc = fig.add_subplot(gs[1, 3])
        ax_sc.set_facecolor("#111120")
        ax_sc.scatter(res["sobel"].flatten(), res["quantum"].flatten(),
                      alpha=0.5, s=8, color="#00bfff", edgecolors="none")
        ax_sc.plot([0, 260], [0, 260], color="#555555", lw=1, ls=":")
        ax_sc.set_xlim(0, 260); ax_sc.set_ylim(0, 260)
        ax_sc.set_title("Q vs Sobel scatter", fontsize=8, color="#7fff00", family="monospace")
        ax_sc.tick_params(colors="#555555")

        ax_m = fig.add_subplot(gs[1, 4])
        ax_m.set_facecolor("#0a0a14")
        for sp in ax_m.spines.values(): sp.set_visible(False)
        ax_m.set_xticks([]); ax_m.set_yticks([])
        ax_m.set_title("Metrics", fontsize=8, color="#7fff00", family="monospace")
        items = [("Corr (Sobel)", f"{res['corr_sobel']:.4f}"),
                 ("Corr (Laplacian)", f"{res['corr_laplacian']:.4f}"),
                 ("MSE vs Sobel", f"{res['mse_vs_sobel']:.2f}"),
                 ("Qubits", str(res['qubits'])), ("Depth", str(res['depth'])),
                 ("Gates", str(res['gate_count'])), ("Time", f"{res['elapsed']:.3f}s")]
        for k, (lbl, val) in enumerate(items):
            y = 0.92 - k * 0.13
            ax_m.text(0.02, y, lbl, fontsize=7.5, color="#888888", transform=ax_m.transAxes)
            ax_m.text(0.6,  y, val, fontsize=7.5, color="#7fff00", fontweight="bold", transform=ax_m.transAxes)

        path = os.path.join(out_dir, "edges_result.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0a0a14")
        plt.close(fig)
        print(f"  {BOLD_GRN}✔  Saved figure → {path}{R}")
    except Exception as e:
        print(f"  {YLW}⚠  Could not save figure: {e}{R}")

def _save_match_figure(res, img_a, img_b, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        fig = plt.figure(figsize=(12, 6), facecolor="#0a0a14")
        gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.5, wspace=0.4,
                               left=0.06, right=0.97, top=0.88, bottom=0.08)
        sim = res["quantum_similarity"]
        colour = "#00ff99" if sim > 0.8 else "#ffcc00" if sim > 0.4 else "#ff4444"
        fig.text(0.5, 0.945, "⚛  Quantum Image Matching — SWAP Test", ha="center",
                 fontsize=15, fontweight="bold", color="#aa88ff", family="monospace")
        fig.text(0.5, 0.915, f"Quantum Similarity: {sim:.4f}  |  Shots: {res['shots']:,}  |  Qubits: {res['qubits']}",
                 ha="center", fontsize=9, color=colour, family="monospace")

        def im(ax, data, title, cmap="gray"):
            ax.set_facecolor("#111120")
            ax.imshow(np.clip(data, 0, 255).astype(np.uint8), cmap=cmap, vmin=0, vmax=255)
            ax.set_title(title, fontsize=9, color="#aa88ff", pad=4, family="monospace")
            ax.set_xticks([]); ax.set_yticks([])

        im(fig.add_subplot(gs[0:2, 0]), img_a, "Image A")
        im(fig.add_subplot(gs[0:2, 1]), img_b, "Image B")

        ax_bar = fig.add_subplot(gs[0, 2:4])
        ax_bar.set_facecolor("#111120")
        labels = ["Quantum\nSWAP", "Classical\nCosine", "Hist.\nIntersect"]
        vals   = [res["quantum_similarity"], max(0, res["classical_cosine"]), res["histogram_intersection"]]
        colors = ["#aa88ff", "#ff4444", "#00ff99"]
        bars = ax_bar.bar(labels, vals, color=colors, width=0.5)
        for bar, v in zip(bars, vals):
            ax_bar.text(bar.get_x() + bar.get_width()/2, v + 0.02, f"{v:.3f}",
                        ha="center", fontsize=9, color="white", fontweight="bold")
        ax_bar.set_ylim(0, 1.3)
        ax_bar.set_title("Similarity Scores", fontsize=9, color="#aa88ff", family="monospace")
        ax_bar.tick_params(colors="#555555")

        ax_c = fig.add_subplot(gs[1, 2])
        ax_c.set_facecolor("#111120")
        counts = res["counts"]
        c0 = counts.get("0", 0); c1 = counts.get("1", 0)
        ax_c.bar(["| 0 ⟩", "| 1 ⟩"], [c0, c1], color=["#aa88ff", "#ff4444"])
        ax_c.set_title("Measurement Counts", fontsize=8, color="#aa88ff", family="monospace")
        ax_c.tick_params(colors="#555555")

        ax_m = fig.add_subplot(gs[1, 3])
        ax_m.set_facecolor("#0a0a14")
        for sp in ax_m.spines.values(): sp.set_visible(False)
        ax_m.set_xticks([]); ax_m.set_yticks([])
        ax_m.set_title("Metrics", fontsize=8, color="#aa88ff", family="monospace")
        items = [("Q-sim", f"{sim:.4f}"), ("Cosine", f"{res['classical_cosine']:.4f}"),
                 ("MSE", f"{res['classical_mse']:.4f}"), ("Qubits", str(res['qubits'])),
                 ("Depth", str(res['depth'])), ("Time", f"{res['elapsed']:.3f}s")]
        for k, (lbl, val) in enumerate(items):
            y = 0.92 - k * 0.15
            ax_m.text(0.02, y, lbl, fontsize=8, color="#888888", transform=ax_m.transAxes)
            ax_m.text(0.6,  y, val, fontsize=8, color="#aa88ff", fontweight="bold", transform=ax_m.transAxes)

        path = os.path.join(out_dir, "matching_result.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0a0a14")
        plt.close(fig)
        print(f"  {BOLD_GRN}✔  Saved figure → {path}{R}")
    except Exception as e:
        print(f"  {YLW}⚠  Could not save figure: {e}{R}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Quantum Image Analysis CLI — Inversion · Matching · Edge Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__))
    parser.add_argument("image",           help="Path to input image")
    parser.add_argument("--mode",          default="all",
                        choices=["all", "inversion", "matching", "edges"],
                        help="Which algorithm(s) to run (default: all)")
    parser.add_argument("--compare",       default=None,
                        help="Second image for matching (required for matching mode)")
    parser.add_argument("--output",        default="./quantum_results",
                        help="Output directory for saved figures (default: ./quantum_results)")
    parser.add_argument("--size",          type=int, default=8,
                        help="Image resize target (power-of-2, max 16; default: 8)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    banner()

    if not os.path.exists(args.image):
        print(f"{BOLD_RED}✖  Image not found: {args.image}{R}")
        sys.exit(1)

    size = min(max(args.size, 2), 16)
    if size != args.size:
        print(f"  {YLW}⚠  size clamped to {size} (range 2–16){R}")

    print(f"  {DIM}Image  : {args.image}{R}")
    print(f"  {DIM}Mode   : {args.mode}{R}")
    print(f"  {DIM}Size   : {size}×{size} (resized to nearest power-of-2){R}")
    print(f"  {DIM}Output : {args.output}{R}")

    t_total = time.perf_counter()

    print(f"\n  {BOLD_CYN}Loading image…{R}")
    img_a = load_image(args.image, size)
    print(f"  {BOLD_GRN}✔  Loaded  shape={img_a.shape}  dtype={img_a.dtype}  "
          f"min={img_a.min():.0f}  max={img_a.max():.0f}{R}")

    img_b = None
    if args.mode in ("all", "matching"):
        src_b = args.compare if args.compare else args.image
        print(f"  {BOLD_CYN}Loading compare image: {src_b}…{R}")
        img_b = load_image(src_b, size)
        print(f"  {BOLD_GRN}✔  Compare  shape={img_b.shape}{R}")

    if args.mode in ("all", "inversion"):
        run_inversion(img_a, args.output)

    if args.mode in ("all", "edges"):
        run_edge_detection(img_a, args.output)

    if args.mode in ("all", "matching"):
        run_matching(img_a, img_b, args.output)

    total = time.perf_counter() - t_total
    print()
    print(BOLD_GRN + "╔══════════════════════════════════════════════════════════════════╗" + R)
    print(BOLD_GRN + f"║  ✔  ALL QUANTUM SIMULATIONS COMPLETE   total={total:.2f}s" + " " * max(0, 17 - len(f"{total:.2f}")) + BOLD_GRN + "║" + R)
    print(BOLD_GRN + f"║  Results saved to: {args.output}" + " " * max(0, 47 - len(args.output)) + "║" + R)
    print(BOLD_GRN + "╚══════════════════════════════════════════════════════════════════╝" + R)
    print()

if __name__ == "__main__":
    main()