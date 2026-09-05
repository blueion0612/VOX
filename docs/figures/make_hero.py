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

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

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


def make(online, offline):
    def draw(T):
        fig, axes = plt.subplots(1, 2, figsize=(figstyle.WIDTH, 3.5),
                                 gridspec_kw={"width_ratios": [1.0, 1.35]})
        ax = axes[0]
        vals = [offline[m][0] for m in MODELS]
        errs = [offline[m][1] for m in MODELS]
        ax.yaxis.grid(True, color=T["line"], linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.bar(LABELS, vals, yerr=errs, capsize=3, color=T["green"], width=0.6,
               error_kw=dict(ecolor=T["muted"], lw=1.1), zorder=3)
        ax.set_title("Public dataset, 5-fold cross-validation", pad=10)
        ax.set_ylim(85, 101)

        ax = axes[1]
        x = np.arange(len(MODELS))
        w = 0.26
        ax.yaxis.grid(True, color=T["line"], linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        for i, (cond, color) in enumerate(zip(ONLINE, [T["muted"], T["green"], T["gold"]])):
            ax.bar(x + (i - 1) * w, [online[cond][m] for m in MODELS], w, label=cond,
                   color=color, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(LABELS)
        ax.set_title("Own recordings, 60 held-out samples", pad=10)
        ax.set_ylim(85, 101)
        # below the axis, where the bars cannot run into it
        leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3,
                        columnspacing=1.1, handlelength=1.2, fontsize=figstyle.SMALL)
        for t in leg.get_texts():
            t.set_color(T["muted"])

        for ax in axes:
            ax.set_ylabel("accuracy, %")
            ax.tick_params(axis="x", length=0, pad=5)
            ax.spines["left"].set_visible(False)
            ax.tick_params(axis="y", length=0)
            figstyle.mono_ticks(ax)
        fig.tight_layout(pad=0.5)
        return fig
    return draw


if __name__ == "__main__":
    on, off = read_online(), read_offline()
    figstyle.save_both(make(on, off), str(HERE / "hero_models"))
