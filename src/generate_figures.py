import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image as PILImage

import inversion
import matching
import edge_detection
from encoding import preprocess, normalise

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "images")
os.makedirs(OUT, exist_ok=True)

BG    = "#ffffff"
FG    = "#0a0a0a"
ACC1  = "#1a1aff"
ACC2  = "#d10000"
ACC3  = "#007a3d"
MID   = "#555555"
LGRAY = "#f0f0f0"
FONT  = "DejaVu Sans"


def _ax(ax, title="", xlabel="", ylabel="", color=FG):
    ax.set_facecolor(LGRAY)
    ax.set_title(title, fontsize=8.5, fontweight="bold", color=color, pad=5, fontfamily=FONT)
    ax.set_xlabel(xlabel, fontsize=7, color=MID)
    ax.set_ylabel(ylabel, fontsize=7, color=MID)
    ax.tick_params(colors=MID, labelsize=6.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("#cccccc")
        sp.set_linewidth(0.8)


def _imshow(ax, img, cmap="gray", title="", color=FG):
    _ax(ax, title=title, color=color)
    ax.imshow(img, cmap=cmap, interpolation="nearest", aspect="equal",
              vmin=0, vmax=255)
    ax.set_xticks([])
    ax.set_yticks([])


def make_test_images(size=16):
    def mk(kind):
        s = size
        if kind == "structured":
            img = np.zeros((s, s))
            img[s//4:3*s//4, s//4:3*s//4] = 200
            img[s//3:2*s//3, s//3:2*s//3] = 255
        elif kind == "gradient":
            img = np.tile(np.linspace(0, 255, s), (s, 1))
        elif kind == "checker":
            x = np.arange(s)
            img = 255 * ((x[:, None] // (s // 4) + x[None, :] // (s // 4)) % 2)
        elif kind == "circle":
            cx, cy = s // 2, s // 2
            Y, X = np.ogrid[:s, :s]
            img = np.where((X - cx)**2 + (Y - cy)**2 <= (s // 3)**2, 200.0, 40.0)
        return preprocess(img, max_dim=s)
    return {
        "structured": mk("structured"),
        "gradient": mk("gradient"),
        "checker": mk("checker"),
        "circle": mk("circle"),
    }


def export_inversion(imgs):
    img = imgs["structured"]
    res = inversion.run(img)
    fig = plt.figure(figsize=(14, 8), facecolor=BG)
    gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.5, wspace=0.4,
                           left=0.06, right=0.97, top=0.88, bottom=0.08)
    fig.text(0.5, 0.945, "Quantum Image Inversion", ha="center",
             fontsize=16, fontweight="bold", color=FG, fontfamily=FONT)
    fig.text(0.5, 0.915, "NEQR Encoding + Pauli-X Gates on Value Register",
             ha="center", fontsize=9, color=MID, fontfamily=FONT)

    _imshow(fig.add_subplot(gs[0, 0]), res["original"], title="Original", color=FG)
    _imshow(fig.add_subplot(gs[0, 1]), res["quantum"], title="Quantum Inverted", color=ACC1)
    _imshow(fig.add_subplot(gs[0, 2]), res["classical"], title="Classical Inverted", color=ACC2)

    diff = np.abs(res["quantum"].astype(float) - res["classical"].astype(float))
    ax_diff = fig.add_subplot(gs[0, 3])
    _imshow(ax_diff, diff, cmap="hot", title="Absolute Difference", color=ACC2)

    ax_hist = fig.add_subplot(gs[1, 0:2])
    _ax(ax_hist, title="Pixel Value Distribution", xlabel="Pixel Value", ylabel="Count", color=FG)
    ax_hist.hist(res["original"].flatten(), bins=32, alpha=0.7, color=FG, label="Original", edgecolor="none")
    ax_hist.hist(res["quantum"].flatten(), bins=32, alpha=0.6, color=ACC1, label="Quantum", edgecolor="none")
    ax_hist.hist(res["classical"].flatten(), bins=32, alpha=0.4, color=ACC2, label="Classical", edgecolor="none")
    ax_hist.legend(fontsize=7)
    ax_hist.set_facecolor(LGRAY)

    ax_err = fig.add_subplot(gs[1, 2])
    _ax(ax_err, title="Error Distribution (Q vs C)", xlabel="Pixel Error", ylabel="Count", color=FG)
    ax_err.hist(diff.flatten(), bins=20, color=ACC1, edgecolor="none", alpha=0.85)
    ax_err.set_facecolor(LGRAY)

    ax_m = fig.add_subplot(gs[1, 3])
    ax_m.set_facecolor(BG)
    for sp in ax_m.spines.values(): sp.set_visible(False)
    ax_m.set_xticks([]); ax_m.set_yticks([])
    metrics = [
        ("MSE",       f"{res['mse']:.6f}"),
        ("PSNR",      f"{res['psnr']:.2f} dB"),
        ("SSIM",      f"{res['ssim']:.6f}"),
        ("Qubits",    f"{res['qubits']}"),
        ("Depth",     f"{res['depth']}"),
        ("Gates",     f"{res['gate_count']}"),
        ("Image",     f"{res['image_size'][0]}×{res['image_size'][1]}"),
        ("Time",      f"{res['elapsed']:.3f}s"),
    ]
    ax_m.set_title("Metrics", fontsize=8.5, fontweight="bold", color=FG, pad=5)
    for k, (label, val) in enumerate(metrics):
        y = 0.92 - k * 0.115
        ax_m.text(0.02, y, label, fontsize=8, color=MID, transform=ax_m.transAxes, fontfamily=FONT)
        ax_m.text(0.55, y, val, fontsize=8, color=FG, fontweight="bold",
                  transform=ax_m.transAxes, fontfamily=FONT)

    path = os.path.join(OUT, "inversion.png")
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")
    return res


def export_matching(imgs):
    pairs = [
        ("structured", "structured", "Identical"),
        ("structured", "checker",    "Different"),
        ("circle",     "circle",     "Identical"),
        ("gradient",   "circle",     "Different"),
    ]
    results = []
    for ka, kb, label in pairs:
        r = matching.run(imgs[ka], imgs[kb], shots=4096)
        results.append({"label": label, "pair": f"{ka} vs {kb}", **r})

    fig = plt.figure(figsize=(16, 10), facecolor=BG)
    gs = gridspec.GridSpec(3, 5, figure=fig, hspace=0.55, wspace=0.4,
                           left=0.05, right=0.97, top=0.90, bottom=0.07)
    fig.text(0.5, 0.948, "Quantum Image Matching", ha="center",
             fontsize=16, fontweight="bold", color=FG, fontfamily=FONT)
    fig.text(0.5, 0.918, "Quantum SWAP Test — Amplitude Encoding — Fidelity Estimation",
             ha="center", fontsize=9, color=MID, fontfamily=FONT)

    for col, ((ka, kb, label), r) in enumerate(zip(pairs, results)):
        ax_a = fig.add_subplot(gs[0, col])
        _imshow(ax_a, imgs[ka], title=ka, color=FG)
        ax_b = fig.add_subplot(gs[1, col])
        _imshow(ax_b, imgs[kb], title=kb, color=FG)
        ax_s = fig.add_subplot(gs[2, col])
        _ax(ax_s, title=f"Similarity ({label})", color=ACC1 if label == "Identical" else ACC2)
        labels_b = ["Quantum\nSWAP", "Classical\nCosine", "Hist.\nIntersect"]
        vals_b   = [r["quantum_similarity"], max(0, r["classical_cosine"]), r["histogram_intersection"]]
        colors_b = [ACC1, ACC2, ACC3]
        bars = ax_s.bar(labels_b, vals_b, color=colors_b, edgecolor="none", width=0.5)
        for bar, v in zip(bars, vals_b):
            ax_s.text(bar.get_x() + bar.get_width()/2, v + 0.02, f"{v:.3f}",
                      ha="center", fontsize=7, color=FG)
        ax_s.set_ylim(0, 1.25)
        ax_s.set_facecolor(LGRAY)

    ax_m = fig.add_subplot(gs[0:2, 4])
    ax_m.set_facecolor(BG)
    for sp in ax_m.spines.values(): sp.set_visible(False)
    ax_m.set_xticks([]); ax_m.set_yticks([])
    ax_m.set_title("Circuit Info", fontsize=8.5, fontweight="bold", color=FG, pad=5)
    r0 = results[0]
    info = [
        ("Qubits",  f"{r0['qubits']}"),
        ("Depth",   f"{r0['depth']}"),
        ("Gates",   f"{r0['gate_count']}"),
        ("Shots",   f"{r0['shots']:,}"),
        ("Time",    f"{r0['elapsed']:.3f}s"),
        ("",""),
        ("Formula", "P(0) = ½ + ½|⟨ψ_A|ψ_B⟩|²"),
        ("Sim",     "2·P(0) − 1"),
    ]
    for k, (label, val) in enumerate(info):
        y = 0.95 - k * 0.115
        ax_m.text(0.02, y, label, fontsize=8, color=MID, transform=ax_m.transAxes)
        ax_m.text(0.45, y, val,   fontsize=8, color=FG, fontweight="bold", transform=ax_m.transAxes)

    path = os.path.join(OUT, "matching.png")
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")
    return results


def export_edges(imgs):
    img = imgs["structured"]
    res = edge_detection.run(img)
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    gs = gridspec.GridSpec(2, 5, figure=fig, hspace=0.5, wspace=0.35,
                           left=0.05, right=0.97, top=0.90, bottom=0.07)
    fig.text(0.5, 0.948, "Quantum Edge Detection", ha="center",
             fontsize=16, fontweight="bold", color=FG, fontfamily=FONT)
    fig.text(0.5, 0.918, "QHED — Quantum Cyclic Shift + Amplitude Difference Operator",
             ha="center", fontsize=9, color=MID, fontfamily=FONT)

    _imshow(fig.add_subplot(gs[0, 0]), res["original"],   title="Original",            color=FG)
    _imshow(fig.add_subplot(gs[0, 1]), res["quantum_h"],  title="Quantum H-Edges", cmap="inferno", color=ACC1)
    _imshow(fig.add_subplot(gs[0, 2]), res["quantum_v"],  title="Quantum V-Edges", cmap="inferno", color=ACC1)
    _imshow(fig.add_subplot(gs[0, 3]), res["quantum"],    title="Quantum Combined", cmap="inferno", color=ACC1)
    _imshow(fig.add_subplot(gs[0, 4]), res["sobel"],      title="Classical Sobel",  cmap="inferno", color=MID)

    ax_lap = fig.add_subplot(gs[1, 0])
    _imshow(ax_lap, res["laplacian"], cmap="inferno", title="Classical Laplacian", color=MID)

    ax_p = fig.add_subplot(gs[1, 1:3])
    _ax(ax_p, title="Row-Midpoint Edge Profile", xlabel="Pixel Column", ylabel="Edge Magnitude")
    mid = res["quantum"].shape[0] // 2
    x = np.arange(res["quantum"].shape[1])
    ax_p.fill_between(x, res["quantum"][mid], alpha=0.35, color=ACC1)
    ax_p.plot(x, res["quantum"][mid],  color=ACC1, lw=1.8, label="Quantum")
    ax_p.fill_between(x, res["sobel"][mid],  alpha=0.2,  color=ACC2)
    ax_p.plot(x, res["sobel"][mid],   color=ACC2, lw=1.8, linestyle="--", label="Sobel")
    ax_p.legend(fontsize=7)
    ax_p.set_facecolor(LGRAY)

    ax_sc = fig.add_subplot(gs[1, 3])
    _ax(ax_sc, title="Quantum vs Sobel (scatter)", xlabel="Sobel", ylabel="Quantum")
    ax_sc.scatter(res["sobel"].flatten(), res["quantum"].flatten(),
                  alpha=0.4, s=6, color=ACC1, edgecolors="none")
    lim = 260
    ax_sc.plot([0, lim], [0, lim], color=MID, lw=1, linestyle=":")
    ax_sc.set_xlim(0, lim); ax_sc.set_ylim(0, lim)
    ax_sc.set_facecolor(LGRAY)

    ax_m = fig.add_subplot(gs[1, 4])
    ax_m.set_facecolor(BG)
    for sp in ax_m.spines.values(): sp.set_visible(False)
    ax_m.set_xticks([]); ax_m.set_yticks([])
    ax_m.set_title("Metrics", fontsize=8.5, fontweight="bold", color=FG, pad=5)
    metrics = [
        ("Corr (Sobel)",    f"{res['corr_sobel']:.4f}"),
        ("Corr (Laplacian)",f"{res['corr_laplacian']:.4f}"),
        ("MSE vs Sobel",    f"{res['mse_vs_sobel']:.2f}"),
        ("Qubits",          f"{res['qubits']}"),
        ("Depth",           f"{res['depth']}"),
        ("Gates",           f"{res['gate_count']}"),
        ("Image",           f"{res['image_size'][0]}×{res['image_size'][1]}"),
        ("Time",            f"{res['elapsed']:.3f}s"),
    ]
    for k, (label, val) in enumerate(metrics):
        y = 0.93 - k * 0.115
        ax_m.text(0.02, y, label, fontsize=7.5, color=MID, transform=ax_m.transAxes)
        ax_m.text(0.65, y, val,   fontsize=7.5, color=FG, fontweight="bold", transform=ax_m.transAxes)

    path = os.path.join(OUT, "edges.png")
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")
    return res


def export_overview(inv_res, match_results, edge_res):
    fig = plt.figure(figsize=(16, 6), facecolor=BG)
    gs = gridspec.GridSpec(1, 5, figure=fig, wspace=0.35,
                           left=0.05, right=0.97, top=0.84, bottom=0.1)
    fig.text(0.5, 0.95, "Quantum Image Processing — Algorithm Comparison",
             ha="center", fontsize=14, fontweight="bold", color=FG, fontfamily=FONT)

    _imshow(fig.add_subplot(gs[0]), inv_res["original"], title="Input Image")
    _imshow(fig.add_subplot(gs[1]), inv_res["quantum"], title="Inverted")
    _imshow(fig.add_subplot(gs[2]), match_results[0]["quantum_similarity"] and inv_res["original"],
            title=f"Match Sim: {match_results[0]['quantum_similarity']:.3f}")
    _imshow(fig.add_subplot(gs[3]), edge_res["quantum"], cmap="inferno", title="Quantum Edges")
    _imshow(fig.add_subplot(gs[4]), edge_res["sobel"],   cmap="inferno", title="Classical Edges")

    path = os.path.join(OUT, "overview.png")
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")


if __name__ == "__main__":
    print("Generating test images...")
    imgs = make_test_images(size=8)
    print("Running inversion...")
    inv_res   = export_inversion(imgs)
    print("Running matching...")
    match_res = export_matching(imgs)
    print("Running edge detection...")
    edge_res  = export_edges(imgs)
    print("Generating overview...")
    export_overview(inv_res, match_res, edge_res)
    print("Done.")