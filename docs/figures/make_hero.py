"""Render the model comparison figure used at the top of the README.

Numbers are parsed out of the training logs under Model/, so the figure cannot
drift from what was actually run.

    python docs/figures/make_hero.py

Writes hero_models.png and hero_models-dark.png.
"""
import io
import os
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

ONLINE = {
    "no filter": ROOT / "Model" / "Online_without_filter" / "Online_log.txt",
    "high-pass": ROOT / "Model" / "Online_with_HPF" / "Online_log.txt",
    "low + high-pass": ROOT / "Model" / "Online_with_LPF_HPF" / "Online_log_lpf.txt",
}
OFFLINE = ROOT / "Model" / "Offline" / "Offline_log.txt"
MODELS = ["bilstm", "gru", "simplecnn", "cnnbilstm", "smalltcn"]
LABELS = ["BiLSTM", "GRU", "CNN", "CNN-BiLSTM", "TCN"]

THEMES = {
    "light": dict(bg="white", ink="#1c2530", muted="#5b6875", grid="#e2e7ec",
                  bars=["#9fb0c0", "#4a7fb5", "#c8683f"], off="#3f7d5a"),
    "dark": dict(bg="#0d1117", ink="#e6edf3", muted="#9198a1", grid="#262c34",
                 bars=["#5b6875", "#6ea8dd", "#e08a5c"], off="#5aa87a"),
}

FINAL = re.compile(
    r"=== Final Test Results for (\w+) ===\s*\n\s*Test Loss\s*:\s*[\d.]+\s*\n"
    r"\s*Test Accuracy\s*:\s*([\d.]+)")


def read_online():
    out = {}
    for cond, path in ONLINE.items():
        s = io.open(path, encoding="utf-8", errors="replace").read()
        out[cond] = {m.group(1): float(m.group(2)) * 100 for m in FINAL.finditer(s)}
    return out


def read_offline():
    s = io.open(OFFLINE, encoding="utf-8", errors="replace").read()
    names = re.findall(r"Saved final model to offline_gesture_(\w+)\.pth", s)
    means = re.findall(r"Mean\s*:\s*Loss=[\d.]+±[\d.]+,\s*Acc=([\d.]+)±([\d.]+)", s)
    return {n: (float(a) * 100, float(sd) * 100) for n, (a, sd) in zip(names, means)}


def render(theme, out_path, online, offline):
    T = THEMES[theme]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.5), dpi=170,
                             gridspec_kw={"width_ratios": [1.0, 1.35]})
    fig.patch.set_facecolor(T["bg"])

    ax = axes[0]
    vals = [offline[m][0] for m in MODELS]
    errs = [offline[m][1] for m in MODELS]
    ax.bar(LABELS, vals, yerr=errs, capsize=3, color=T["off"], width=0.6,
           error_kw=dict(ecolor=T["muted"], lw=1.1))
    ax.set_title("Public dataset, 5-fold cross-validation", fontsize=10.6,
                 color=T["ink"], fontweight="bold", pad=10)
    ax.set_ylim(85, 101)

    ax = axes[1]
    x = np.arange(len(MODELS))
    w = 0.26
    for i, (cond, colour) in enumerate(zip(ONLINE, T["bars"])):
        ax.bar(x + (i - 1) * w, [online[cond][m] for m in MODELS], w,
               label=cond, color=colour)
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS)
    ax.set_title("Own recordings, 60 held-out samples", fontsize=10.6,
                 color=T["ink"], fontweight="bold", pad=10)
    ax.set_ylim(85, 101)
    leg = ax.legend(fontsize=8.6, frameon=False, loc="lower right", ncol=3,
                    columnspacing=1.1, handlelength=1.2)
    for t in leg.get_texts():
        t.set_color(T["muted"])

    for ax in axes:
        ax.set_ylabel("accuracy %", fontsize=9, color=T["muted"])
        ax.set_facecolor(T["bg"])
        ax.tick_params(colors=T["muted"], labelsize=9)
        ax.grid(axis="y", color=T["grid"], lw=0.9)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(T["grid"])

    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=170, bbox_inches="tight", facecolor=T["bg"])
    plt.close(fig)
    print("wrote", out_path)


if __name__ == "__main__":
    on, off = read_online(), read_offline()
    render("light", HERE / "hero_models.png", on, off)
    render("dark", HERE / "hero_models-dark.png", on, off)
