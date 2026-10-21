"""Build "FIGHTEX — Economic Simulation Architecture: Engineering Case Study" (English, A4, 7 pages).

Local, offline script. It reads only the synthetic CSV files in ./data (see generate_synthetic_data.py), renders the
charts with matplotlib and lays out the report with ReportLab. It does not connect to MCP or production systems,
does not import the private FIGHTEX/HalFin code, and does not run any simulation of the real engine.

Every chart that shows data carries the label
    "Illustrative synthetic data — not actual FIGHTEX audit results."

Usage:
    python generate_synthetic_data.py      # optional: rewrites ./data (identical output for the fixed seed)
    python build_case_study.py             # writes ../../docs/FIGHTEX_Architecture_Case_Study_EN.pdf
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent.parent / "docs" / "FIGHTEX_Architecture_Case_Study_EN.pdf"

TITLE = "FIGHTEX — Economic Simulation Architecture"
SUBTITLE = "Engineering Case Study"
SYNTH = "Illustrative synthetic data — not actual FIGHTEX audit results."
PAGES = 7

# Okabe–Ito palette (colour-blind safe) plus neutrals
BLUE, ORANGE, GREEN, VERM, PURPLE, SKY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"
INK, MUTED, GRID, PANEL, NAVY = "#1F2937", "#6B7280", "#E5E7EB", "#F3F4F6", "#12355B"

# ---------------------------------------------------------------------------------------------------------------------
# fonts (DejaVu Sans ships with matplotlib; used for both the charts and the PDF text)
# ---------------------------------------------------------------------------------------------------------------------
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "DejaVuSansMono.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-Bold")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.labelsize": 7.5,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 7, "figure.dpi": 100, "savefig.dpi": 200,
    "axes.titlelocation": "left", "axes.titlepad": 6,
})

# ---------------------------------------------------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------------------------------------------------


def load(name: str) -> dict[str, np.ndarray]:
    with (DATA / name).open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out: dict[str, list] = {k: [] for k in rows[0]}
    for r in rows:
        for k, v in r.items():
            out[k].append(v)
    result = {}
    for k, v in out.items():
        try:
            result[k] = np.array([float(x) for x in v])
        except ValueError:
            result[k] = np.array(v, dtype=object)
    return result


def synth_note(fig, y: float = 0.012) -> None:
    fig.text(0.012, y, SYNTH, fontsize=6.5, color=MUTED, style="italic", ha="left", va="bottom")


# ---------------------------------------------------------------------------------------------------------------------
# diagram helpers
# ---------------------------------------------------------------------------------------------------------------------


def box(ax, x, y, w, h, text, fc=PANEL, ec="#9CA3AF", fs=7.2, bold=False, color=INK, lw=0.8, round_=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color="#4B5563", style="-|>", lw=0.9, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=7, lw=lw, color=color, connectionstyle=f"arc3,rad={rad}", linestyle=ls,
                                 shrinkA=0, shrinkB=0))


def blank_axes(fig, rect):
    ax = fig.add_axes(rect)
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    return ax


# ---------------------------------------------------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------------------------------------------------


def fig_architecture(path: Path) -> None:
    fig = plt.figure(figsize=(7.15, 3.65))
    ax = blank_axes(fig, [0, 0, 1, 1])
    ax.set_ylim(0, 64)
    c_if, c_orch, c_eng, c_store = "#DCEBF7", "#E5E7EB", "#FCEBC8", "#D5EFE6"
    ax.text(1, 62, "Interfaces", fontsize=7, color=MUTED, fontweight="bold")
    box(ax, 1, 52, 26, 8, "Streamlit dashboard\n(local analyst UI)", c_if)
    box(ax, 30, 52, 20, 8, "Command-line\ninterface", c_if)
    box(ax, 53, 52, 28, 8, "MCP clients\n(AI assistants)", c_if)
    box(ax, 53, 40.5, 28, 8, "Access gateway\nroles · default deny · rate limits", c_orch, fs=6.8)
    box(ax, 1, 40.5, 26, 8, "Dashboard controller", c_orch)
    for x in (14, 40):
        arrow(ax, x, 52, x if x == 14 else 40, 48.5)
    arrow(ax, 67, 52, 67, 48.5)
    ax.text(17, 37.4, "Application layer", fontsize=7, color=MUTED, fontweight="bold")
    box(ax, 1, 25.5, 80, 10.5, "SimulatorService — one orchestration layer for every interface\nscenario lifecycle · resource preflight · result cache · exports", c_orch, bold=True, fs=7.4)
    arrow(ax, 14, 40.5, 14, 36)
    arrow(ax, 40, 52, 40, 36.2, rad=0.0)
    arrow(ax, 67, 40.5, 67, 36)
    box(ax, 84, 40.5, 15, 19.5, "Validated\nconfiguration\n\nversioned baseline\nprovenance\nparameter hash", c_store, fs=6.5)
    box(ax, 84, 12.5, 15, 23.5, "Persistence\n(SQLite)\n\nscenarios\nimmutable\nsnapshots\nrun ledger", c_store, fs=6.5)
    arrow(ax, 84, 45, 81, 33, rad=-0.15)
    arrow(ax, 81, 29, 84, 24, color="#4B5563")
    arrow(ax, 84, 24, 81, 29, color="#4B5563")
    ax.text(1, 22.4, "Computation layer — independent of UI, transport and database", fontsize=7, color=MUTED, fontweight="bold")
    box(ax, 1, 11, 80, 9.2, "Simulation runner  ·  seeded, named random streams  ·  result digest", c_eng, bold=True, fs=7.4)
    arrow(ax, 70, 25.5, 70, 20.2)
    names = ["Daily player &\ncard economy", "Tournament /\nMonte Carlo", "Bot-farm\nanalysis", "Financial\nmodeling", "Reconciliation\n& invariants"]
    w = 15.2
    for i, n in enumerate(names):
        x = 1 + i * (w + 1)
        box(ax, x, 0.8, w, 8.2, n, c_eng if i < 4 else "#F8D9CC", fs=6.6)
        arrow(ax, x + w / 2, 11, x + w / 2, 9.0)
    fig.savefig(path)
    plt.close(fig)


def fig_multi_account_schema(path: Path) -> None:
    fig = plt.figure(figsize=(7.15, 3.2))
    ax = blank_axes(fig, [0, 0, 1, 1])
    ax.set_ylim(0, 50)
    c_org, c_bot, c_core, c_out = "#DCEBF7", "#F8D9CC", "#E5E7EB", "#D5EFE6"
    ax.text(1, 48.3, "Actors", fontsize=7, color=MUTED, fontweight="bold")
    segs = ["F2P active players", "Collectors", "Paying players", "Crafters", "Traders"]
    for i, name in enumerate(segs):
        box(ax, 1, 41 - i * 6.4, 24, 5.2, name, c_org, fs=6.8)
    ax.text(13, 12.9, "organic population (strategy mix)", ha="center", fontsize=6.3, color=MUTED, style="italic")
    box(ax, 33, 17, 34, 28.5, "Shared daily economic state\n\nvirtual-card supply and expiry\nmarketplace order book\nstaking and FP ledger\ntournament pools and payouts\nfees and withdrawals", c_core, fs=6.9)
    ax.text(50, 19.4, "same rules · same seed · same day loop", ha="center", fontsize=6.2, color=NAVY, style="italic")
    box(ax, 75, 31, 24, 14.5, "Multi-account actors\n(bot-farm slice)\nN accounts · entry route\nsetup and running costs", c_bot, fs=6.6)
    ax.text(87, 28.2, "selected from the same population", ha="center", fontsize=6.2, color=MUTED, style="italic")
    for i in range(5):
        arrow(ax, 25, 43.6 - i * 6.4, 33, 33 + (i - 2) * 2.4, color="#6B7280", lw=0.7)
    arrow(ax, 75, 40, 67, 40, color=VERM)
    arrow(ax, 67, 36, 75, 36, color="#6B7280", lw=0.7)
    ax.text(1, 9.6, "Outputs per account and per market", fontsize=7, color=MUTED, fontweight="bold")
    outs = ["3rd card acquired\n(day)", "first tournament\nentry (day)", "first prize\n(day)", "costs · market\nproceeds · fees", "withdrawals ·\nresidual inventory"]
    for i, o in enumerate(outs):
        box(ax, 1 + i * 20.15, 0.4, 18.4, 7.4, o, c_out, fs=6.3)
    arrow(ax, 50, 17, 50, 8.0, color="#6B7280", lw=0.8)
    fig.savefig(path)
    plt.close(fig)


def fig_multi_account_charts(path: Path) -> None:
    flow = load("order_flow.csv")
    acc = load("multi_account.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 2.95), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    ax.stackplot(flow["day"], flow["organic_orders"], flow["multi_account_orders"], colors=[SKY, VERM], alpha=0.9, labels=["Organic players", "Multi-account actors"])
    ax.set_title("(a) Buy orders in one shared market")
    ax.set_xlabel("Simulation day")
    ax.set_ylabel("Open buy orders per day")
    ax.set_ylim(0, 530)
    ax.legend(loc="upper left")
    ax.set_xlim(1, 180)
    ax = axes[1]
    groups = ["organic", "multi_account"]
    data_entry = [acc["first_tournament_day"][acc["actor_group"] == g] for g in groups]
    data_prize = [acc["first_prize_day"][acc["actor_group"] == g] for g in groups]
    pos = np.array([1, 2])
    bp1 = ax.boxplot(data_entry, positions=pos - 0.19, widths=0.3, patch_artist=True, showfliers=False, medianprops={"color": INK, "lw": 1})
    bp2 = ax.boxplot(data_prize, positions=pos + 0.19, widths=0.3, patch_artist=True, showfliers=False, medianprops={"color": INK, "lw": 1})
    for b in bp1["boxes"]:
        b.set(facecolor=BLUE, alpha=0.85, edgecolor=BLUE)
    for b in bp2["boxes"]:
        b.set(facecolor=ORANGE, alpha=0.9, edgecolor=ORANGE)
    for bp in (bp1, bp2):
        for k in ("whiskers", "caps"):
            for ln in bp[k]:
                ln.set(color=MUTED, lw=0.8)
    ax.set_xticks(pos, ["Organic", "Multi-account"])
    ax.set_ylabel("Day of milestone")
    ax.set_ylim(0, 185)
    ax.set_title("(b) Per-account milestone timing")
    ax.legend([bp1["boxes"][0], bp2["boxes"][0]], ["First tournament entry", "First prize"], loc="upper left")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    synth_note(fig)
    fig.savefig(path)
    plt.close(fig)


def fig_marketplace(path: Path) -> None:
    m = load("marketplace.csv")
    d = m["day"]
    fig, axes = plt.subplots(3, 1, figsize=(7.15, 6.0), sharex=True, gridspec_kw={"height_ratios": [1.15, 1, 0.95]})
    ax = axes[0]
    ax.plot(d, m["listed_supply"], color=BLUE, lw=1.4, label="Listed supply (cards)")
    ax.plot(d, m["demand_orders"], color=ORANGE, lw=1.4, label="Open demand orders")
    ax.set_title("(a) Supply and demand orders")
    ax.set_ylabel("Count")
    ax.legend(loc="center right", ncol=1)
    ax.annotate("demand orders are not trades", xy=(120, m["demand_orders"][119]), xytext=(88, 640), fontsize=6.8, color=MUTED, arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6})
    ax = axes[1]
    ax.bar(d, m["executed_trades"], color=GREEN, width=0.85, alpha=0.9, label="Executed trades per day")
    roll = np.convolve(m["executed_trades"], np.ones(7) / 7, mode="valid")
    ax.plot(d[6:], roll, color=INK, lw=1.1, label="7-day average")
    ax.set_title("(b) Executed trades")
    ax.set_ylabel("Trades per day")
    ax.set_ylim(0, 215)
    ax.legend(loc="upper left", ncol=2)
    ax = axes[2]
    ax.plot(d, m["vwap"], color=PURPLE, lw=1.4, label="Volume-weighted average price")
    ax.plot(d, m["floor_price"], color=MUTED, lw=1, ls="--", label="Floor price")
    ax.set_title("(c) Price discovery")
    ax.set_ylabel("Price (notional unit)")
    ax.set_xlabel("Simulation day")
    ax.set_ylim(0.4, 1.55)
    ax.legend(loc="upper left", ncol=2)
    ax.set_xlim(1, 180)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    synth_note(fig)
    fig.savefig(path)
    plt.close(fig)


def fig_botfarm(path: Path) -> tuple[float, float]:
    sc = load("botfarm_scenarios.csv")
    liq = load("liquidation_curve.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.9), gridspec_kw={"width_ratios": [1, 1.12]})
    ax = axes[0]
    n = len(sc["scenario"])
    x = np.arange(n)
    width = 0.26
    series = [("Realized value", sc["realized_value"], BLUE), ("Liquidation-adjusted", sc["liquidation_adjusted_value"], ORANGE), ("Theoretical value", sc["theoretical_value"], GRID)]
    for i, (lab, vals, col) in enumerate(series):
        bars = ax.bar(x + (i - 1) * width, vals, width, label=lab, color=col, edgecolor="#9CA3AF" if col == GRID else col, lw=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 4, f"{v:.0f}", ha="center", fontsize=6.2, color=INK)
    ax.axhline(100, color=VERM, lw=0.9, ls="--", label="Setup + running cost")
    ax.set_xticks(x, ["Route A\nbuy on market", "Route B\npacks + craft", "Route C\nreferral-style"], fontsize=6.6)
    ax.set_ylabel("Value per 100 accounts (notional units)")
    ax.set_title("(a) Three valuation lenses")
    ax.set_ylim(0, 400)
    ax.legend(loc="upper right", fontsize=6.4)
    ax = axes[1]
    colors_ = {10: VERM, 20: ORANGE, 40: GREEN}
    theo = float(liq["theoretical_value"][0])
    for depth in (10, 20, 40):
        sel = liq["market_sales_per_day"] == depth
        ax.plot(liq["window_days"][sel], liq["liquidation_adjusted_value"][sel], color=colors_[depth], lw=1.5, label=f"Market absorbs {depth} sales / day")
    ax.axhline(theo, color=INK, lw=1, ls="--")
    ax.text(362, theo + 16, "theoretical value at floor, net of fee", fontsize=6.3, ha="right", color=INK)
    ax.axvline(45, color=MUTED, lw=0.8, ls=":")
    ax.text(50, 1022, "45 days: 900 cards at 20 sales / day", fontsize=6.3, color=MUTED, va="bottom")
    ax.set_xlabel("Liquidation window after the horizon (days)")
    ax.set_ylabel("Proceeds from 1,000 residual cards")
    ax.set_title("(b) Liquidation sensitivity")
    ax.set_xlim(0, 365)
    ax.set_ylim(0, 1130)
    ax.legend(loc="lower right", fontsize=6.4)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    synth_note(fig)
    fig.savefig(path)
    plt.close(fig)
    sel = (liq["market_sales_per_day"] == 20) & (liq["window_days"] == 45)
    return theo, float(liq["liquidation_adjusted_value"][sel][0])


def fig_finance(path: Path) -> tuple[float, int]:
    f = load("finance_monthly.csv")
    mth = f["month"]
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 4.2), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    bottoms = np.zeros(mth.size)
    for key, lab, col in (("packs", "Pack sales", BLUE), ("slots", "Slot sales", SKY), ("ads", "Advertising", GREEN), ("marketplace_fees", "Marketplace fees", PURPLE)):
        ax.bar(mth, f[key], bottom=bottoms, width=0.78, color=col, label=lab)
        bottoms += f[key]
    neg = np.zeros(mth.size)
    for key, lab, col in (("prizes", "Prize payouts", VERM), ("marketing", "Marketing", ORANGE), ("operations", "Operations", "#9CA3AF")):
        ax.bar(mth, -f[key], bottom=-neg, width=0.78, color=col, label=lab)
        neg += f[key]
    ax.plot(mth, f["net_cash_flow"], color=INK, lw=1.4, marker="o", ms=2.6, label="Net cash flow")
    ax.axhline(0, color=INK, lw=0.7)
    ax.set_title("(a) Monthly revenue (up) and expenses (down)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Notional units (thousands)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=6.2, columnspacing=1.0, handlelength=1.2)
    ax.set_xlim(0.2, 24.8)
    ax = axes[1]
    cum = f["cumulative_cash_flow"]
    ax.plot(mth, cum, color=BLUE, lw=1.6)
    ax.fill_between(mth, cum, 0, where=cum < 0, color=VERM, alpha=0.1)
    i = int(np.argmin(cum))
    ax.scatter([mth[i]], [cum[i]], color=VERM, zorder=5, s=18)
    ax.annotate(f"minimum cumulative cash\n(month {int(mth[i])})", xy=(mth[i], cum[i]), xytext=(mth[i] - 3.5, cum[i] - 260), fontsize=6.5, ha="center",
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6})
    ax.axhline(0, color=INK, lw=0.7)
    ax.set_title("(b) Cumulative cash flow")
    ax.set_xlabel("Month")
    ax.set_ylabel("Notional units (thousands)")
    ax.set_xlim(1, 24)
    ax.set_ylim(cum.min() - 420, 80)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    synth_note(fig)
    fig.savefig(path)
    plt.close(fig)
    return float(cum[i]), int(mth[i])


def fig_tornado(path: Path) -> None:
    s = load("sensitivity.csv")
    spread = load("seed_spread.csv")
    sigma = float(np.std(spread["deviation_pct"], ddof=1))
    band = 2 * sigma
    low, high = s["effect_at_low_pct"], s["effect_at_high_pct"]
    order = np.argsort(np.maximum(np.abs(low), np.abs(high)))
    names = [s["driver"][i] for i in order]
    low, high = low[order], high[order]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.15, 4.6), gridspec_kw={"width_ratios": [1.65, 1]})
    y = np.arange(len(names))
    ax.axvspan(-band, band, color=GRID, alpha=0.9, lw=0, zorder=0, label="Simulation noise band (±2σ across seeds)")
    ax.barh(y, low, color=BLUE, height=0.62, label="Parameter at test-low value", zorder=3)
    ax.barh(y, high, color=ORANGE, height=0.62, label="Parameter at test-high value", zorder=3)
    ax.axvline(0, color=INK, lw=0.9, zorder=4)
    for yy, a, b in zip(y, low, high):
        for v in (a, b):
            ax.text(v + (1.0 if v >= 0 else -1.0), yy, f"{v:+.0f}%", va="center", ha="left" if v >= 0 else "right", fontsize=6.4)
    ax.set_yticks(y, names, fontsize=6.8)
    ax.set_xlabel("Change in the headline result vs. base case (%)")
    ax.set_title("(a) One-factor-at-a-time (tornado)")
    ax.set_xlim(-58, 58)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1, fontsize=6.4)
    seeds = spread["seed_index"]
    dev = spread["deviation_pct"]
    ax2.axhspan(-band, band, color=GRID, alpha=0.9, lw=0, zorder=0)
    ax2.scatter(seeds, dev, s=11, color=BLUE, zorder=3)
    ax2.axhline(0, color=INK, lw=0.8)
    ax2.axhline(11, color=ORANGE, lw=1.3)
    ax2.text(1, 12.2, "driver effect +11%: above noise", fontsize=6.4, color=INK)
    ax2.axhline(2.5, color=VERM, lw=1.3, ls="--")
    ax2.text(1, 4.0, "driver effect +2.5%: inside noise", fontsize=6.4, color=INK)
    ax2.set_ylim(-9, 16)
    ax2.set_xlabel("Seed index (same parameters)")
    ax2.set_ylabel("Deviation of the base-case result (%)")
    ax2.set_title("(b) Noise band from seeds")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    synth_note(fig)
    fig.savefig(path)
    plt.close(fig)


def fig_pipeline(path: Path) -> None:
    fig = plt.figure(figsize=(7.15, 3.3))
    ax = blank_axes(fig, [0, 0, 1, 1])
    ax.set_ylim(0, 42)
    steps = [
        ("1  Inputs", "baseline + overrides\nparameter provenance\nseed", "#DCEBF7"),
        ("2  Parameter hash", "canonical JSON\nSHA-256 of the\nfull parameter set", "#E5E7EB"),
        ("3  Simulation", "named random\nstreams per process\ndaily loop", "#FCEBC8"),
        ("4  Result digest", "SHA-256 of summary\nand tables, rounded\n(runtime excluded)", "#FCEBC8"),
    ]
    steps2 = [
        ("5  Immutable record", "configuration snapshot\nappend-only run ledger\nversion stamps", "#D5EFE6"),
        ("6  Audit kit", "report + manifest with\nSHA-256 per file\nkit hash", "#D5EFE6"),
        ("7  Controlled access", "role-based views\nread-only operation\nintegrity checks", "#DCEBF7"),
    ]
    w, h = 22, 14
    for i, (t, d, c) in enumerate(steps):
        x = 1 + i * 25
        box(ax, x, 25, w, h, "", c)
        ax.text(x + w / 2, 36.4, t, ha="center", fontsize=7.2, fontweight="bold")
        ax.text(x + w / 2, 30.6, d, ha="center", va="center", fontsize=6.2, linespacing=1.3)
        if i < 3:
            arrow(ax, x + w, 32, x + 25, 32)
    for i, (t, d, c) in enumerate(steps2):
        x = 13.5 + i * 25
        box(ax, x, 3, w, h, "", c)
        ax.text(x + w / 2, 14.4, t, ha="center", fontsize=7.2, fontweight="bold")
        ax.text(x + w / 2, 8.6, d, ha="center", va="center", fontsize=6.2, linespacing=1.3)
        if i < 2:
            arrow(ax, x + w, 10, x + 25, 10)
    ax.plot([87, 87, 24.5], [25, 21.5, 21.5], color="#6B7280", lw=0.9)
    arrow(ax, 24.5, 21.5, 24.5, 17.1, color="#6B7280")
    ax.text(56, 21.5, "same inputs + same seed  →  same digest", ha="center", va="center", fontsize=6.6, color=NAVY, style="italic", bbox={"fc": "white", "ec": "none", "pad": 1.5})
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------------
# toy determinism demo (a deliberately tiny model; NOT the FIGHTEX engine)
# ---------------------------------------------------------------------------------------------------------------------


def toy_run(seed: int, params: dict) -> dict:
    """Tiny seeded economy used only to demonstrate hashing and determinism."""
    root = np.random.SeedSequence(seed)
    streams = {name: np.random.default_rng(s) for name, s in zip(("players", "market", "tournaments"), root.spawn(3))}
    cash, balance = 0.0, []
    for _day in range(60):
        buyers = streams["players"].binomial(params["players"], params["buy_prob"])
        price = params["price"] * (1 + 0.02 * streams["market"].standard_normal())
        prize = params["prize"] if streams["tournaments"].random() < 0.5 else 0.0
        cash += buyers * price - prize
        balance.append(round(float(cash), 6))
    summary = {"final_cash": balance[-1], "min_cash": min(balance)}
    params_hash = hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    digest = hashlib.sha256(json.dumps({"params_hash": params_hash, "summary": summary, "table": balance}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return {"params_hash": params_hash, "digest": digest, "final_cash": summary["final_cash"]}


# ---------------------------------------------------------------------------------------------------------------------
# document
# ---------------------------------------------------------------------------------------------------------------------
W, H = A4
M = 17 * mm
CONTENT_W = W - 2 * M

ST = {
    "title": ParagraphStyle("title", fontName="Body-Bold", fontSize=18.5, leading=23, textColor=colors.HexColor(NAVY), spaceAfter=2),
    "subtitle": ParagraphStyle("subtitle", fontName="Body", fontSize=12, leading=15, textColor=colors.HexColor(MUTED), spaceAfter=4),
    "meta": ParagraphStyle("meta", fontName="Body", fontSize=7.4, leading=10, textColor=colors.HexColor(MUTED), spaceAfter=7),
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=14.5, leading=18, textColor=colors.HexColor(NAVY), spaceBefore=0, spaceAfter=5),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=9.4, leading=12, textColor=colors.HexColor(INK), spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Body", fontSize=8.6, leading=12.2, textColor=colors.HexColor(INK), alignment=TA_LEFT, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="Body", fontSize=8.4, leading=11.6, leftIndent=10, bulletIndent=0, textColor=colors.HexColor(INK), spaceAfter=1.5),
    "caption": ParagraphStyle("caption", fontName="Body-Italic", fontSize=7, leading=9.4, textColor=colors.HexColor(MUTED), spaceBefore=2, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.5, leading=9.8, textColor=colors.HexColor(INK)),
    "cellb": ParagraphStyle("cellb", fontName="Body-Bold", fontSize=7.5, leading=9.8, textColor=colors.HexColor(INK)),
    "cellh": ParagraphStyle("cellh", fontName="Body-Bold", fontSize=7.5, leading=9.8, textColor=colors.white),
    "mono": ParagraphStyle("mono", fontName="Mono", fontSize=7.2, leading=9.6, textColor=colors.HexColor(INK)),
    "note": ParagraphStyle("note", fontName="Body-Italic", fontSize=7.4, leading=10, textColor=colors.HexColor(MUTED)),
}


def P(text, style="body"):
    return Paragraph(text, ST[style])


def bullets(items):
    return [Paragraph(t, ST["bullet"], bulletText="•") for t in items]


def table(rows, widths, header=True, mono_cols=()):
    data = []
    for r_i, row in enumerate(rows):
        cells = []
        for c_i, cell in enumerate(row):
            if r_i == 0 and header:
                style = "cellh"
            elif c_i == 0:
                style = "cellb"
            elif c_i in mono_cols:
                style = "mono"
            else:
                style = "cell"
            cells.append(Paragraph(cell, ST[style]))
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(GRID)), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]
    if header:
        style_cmds += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY))]
        style_cmds += [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F9FAFB")) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(style_cmds))
    return t


def image(path: Path, width=CONTENT_W):
    from PIL import Image as PILImage  # Pillow is installed with matplotlib

    with PILImage.open(path) as im:
        w, h = im.size
    return Image(str(path), width=width, height=width * h / w)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 6.8)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(M, H - 11 * mm, f"{TITLE}  ·  {SUBTITLE}")
    canvas.drawRightString(W - M, H - 11 * mm, "Public architecture overview")
    canvas.setStrokeColor(colors.HexColor(GRID))
    canvas.setLineWidth(0.5)
    canvas.line(M, H - 13 * mm, W - M, H - 13 * mm)
    canvas.line(M, 12.5 * mm, W - M, 12.5 * mm)
    canvas.drawString(M, 8.2 * mm, "Illustrative figures use synthetic data. Not an audit report, forecast or security certification.")
    canvas.drawRightString(W - M, 8.2 * mm, f"Page {doc.page} of {PAGES}")
    canvas.restoreState()


def build(tmp: Path) -> None:
    f_arch, f_ma_s, f_ma_c = tmp / "arch.png", tmp / "ma_schema.png", tmp / "ma_charts.png"
    f_mk, f_bf, f_fin, f_tor, f_pipe = tmp / "market.png", tmp / "botfarm.png", tmp / "finance.png", tmp / "tornado.png", tmp / "pipeline.png"
    fig_architecture(f_arch)
    fig_multi_account_schema(f_ma_s)
    fig_multi_account_charts(f_ma_c)
    fig_marketplace(f_mk)
    theo, at45 = fig_botfarm(f_bf)
    min_cum, min_month = fig_finance(f_fin)
    fig_tornado(f_tor)
    fig_pipeline(f_pipe)

    runs = [("Run A", 42, {"players": 500, "buy_prob": 0.03, "price": 5.0, "prize": 700.0}),
            ("Run B (repeat of A)", 42, {"players": 500, "buy_prob": 0.03, "price": 5.0, "prize": 700.0}),
            ("Run C (different seed)", 43, {"players": 500, "buy_prob": 0.03, "price": 5.0, "prize": 700.0}),
            ("Run D (one parameter changed)", 42, {"players": 500, "buy_prob": 0.03, "price": 5.0, "prize": 750.0})]
    results = [(n, s, toy_run(s, p)) for n, s, p in runs]
    base_digest = results[0][2]["digest"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18 * mm, bottomMargin=17 * mm,
                          title=f"{TITLE} — {SUBTITLE}", author="FIGHTEX architecture overview", subject="Engineering case study (synthetic illustrations)",
                          keywords="simulation, tokenomics, marketplace liquidity, reproducibility", creator="build_case_study.py", invariant=True)
    frame = Frame(M, 17 * mm, CONTENT_W, H - 17 * mm - 18 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=on_page)])
    s: list = []
    SP = Spacer

    # ---- page 1 -------------------------------------------------------------------------------------------------------
    s += [P(TITLE, "title"), P(SUBTITLE, "subtitle"),
          P("Public companion to the <b>fightex-economic-simulation-architecture</b> repository · English edition · synthetic illustrations only", "meta"),
          P("1. Architecture Overview", "h1"),
          P("FIGHTEX is a Python simulation architecture for a fantasy-sports collectible game economy. It models player behavior, virtual cards, staking, crafting, "
            "marketplace trading, tournament payouts and platform finances day by day, and exposes the same engine to analysts (dashboard, CLI) and to AI assistants (MCP). "
            "The private implementation, customer parameters and audit results are intentionally not part of this document."),
          image(f_arch),
          P("Figure 1. Component diagram (conceptual). Colors group interfaces, orchestration, computation and persistence.", "caption"),
          P("Design decisions that shape the system", "h2"),
          table([["Decision", "What it means in practice"],
                 ["One engine, many interfaces", "Dashboard, CLI and MCP converge on one application service and one runner, so formulas cannot diverge between channels. "
                  "An AI assistant interprets structured results; the arithmetic stays in Python."],
                 ["Evidence over narrative", "Every number is tied to a versioned configuration, a seed and a result digest. Inputs distinguish customer-defined rules from "
                  "unverified behavioral assumptions."],
                 ["Default-deny access", "Roles are assigned by the server, never by tool arguments. Tools and data are exposed through an explicit allow-list; "
                  "an operational read-only mode can disable all calculations."],
                 ["Resource-aware execution", "Requests are validated and cost-estimated before they run; oversized requests are rejected instead of being started."]],
                [CONTENT_W * 0.25, CONTENT_W * 0.75]),
          SP(1, 6),
          P("Technology: Python 3.12+, NumPy, SciPy, Pandas, Pydantic, SQLite, Streamlit, pytest and Hypothesis, the Python MCP SDK; Docker Compose and Nginx for server deployment.", "note"),
          P("In this document", "h2"),
          table([["Page", "Topic", "Visualization"],
                 ["2", "Multi-account simulation", "Shared-state diagram; order flow; milestones"],
                 ["3", "Marketplace liquidity", "Supply / demand / executed trades"],
                 ["4", "Bot-farm economics", "Three valuation lenses; liquidation curves"],
                 ["5", "Financial modeling", "Revenue / expenses / cash flow"],
                 ["6", "Sensitivity analysis", "Tornado chart; seed-spread plot"],
                 ["7", "Reproducibility", "Seed → simulation → digest → audit"]],
                [CONTENT_W * 0.08, CONTENT_W * 0.37, CONTENT_W * 0.55]),
          PageBreak()]

    # ---- page 2 -------------------------------------------------------------------------------------------------------
    s += [P("2. Multi-account Simulation", "h1"),
          P("Coordinated multi-account behavior is only meaningful inside the economy it exploits. The bot-farm analysis therefore does not use a stand-alone ROI spreadsheet that "
            "assumes unlimited buyers: multi-account actors are a slice of the <b>same simulated population</b>, running through the <b>same daily state</b> as organic players — "
            "the same card supply and expiry, order book, staking ledger, tournament pools, fees and withdrawal rules."),
          image(f_ma_s),
          P("Figure 2. Organic and multi-account actors share one economic state (conceptual diagram).", "caption"),
          image(f_ma_c),
          P("Figure 3. Illustrative output of a shared-economy run: (a) both groups place orders in one market; (b) per-account milestone timing. " + SYNTH, "caption"),
          P("What the analysis can answer", "h2")]
    s += bullets([
        "<b>Per-account milestones:</b> day of the third card, first tournament entry and first prize, plus operating and setup expenses.",
        "<b>Market feedback:</b> multi-account demand competes with organic demand, so purchases, fees and sell-offs change the prices the same accounts later face.",
        "<b>Entry-route comparison:</b> alternative ways to acquire cards can be compared without publishing proprietary behavioral coefficients.",
        "<b>Distribution, not just a mean:</b> per-account outcome distributions show how much of a result depends on a few lucky accounts."])
    s += [PageBreak()]

    # ---- page 3 -------------------------------------------------------------------------------------------------------
    s += [P("3. Marketplace Liquidity", "h1"),
          P("A card is only worth what the market can absorb. The marketplace analysis separates what is <i>offered</i>, what is <i>wanted</i> and what actually <i>trades</i>, "
            "and it does not assume that market-wide demand is exclusively available to one seller."),
          table([["Quantity", "Definition used in the analysis"],
                 ["Listed supply", "Cards currently offered for sale, by rarity."],
                 ["Demand orders", "Open buy intent at acceptable prices. It is an upper bound on trades, not a trade count."],
                 ["Executed trades", "Matches between a listing and a demand order within a day; the only flow that creates fees and proceeds."],
                 ["Volume-weighted price", "Average executed price weighted by volume; compared with the floor price to see price discovery and depth."]],
                [CONTENT_W * 0.25, CONTENT_W * 0.75]),
          SP(1, 6), image(f_mk),
          P("Figure 4. Supply, demand orders, executed trades and price for one rarity over 180 simulated days. " + SYNTH, "caption"),
          P("Reading the chart", "h2")]
    s += bullets([
        "In this illustration listed supply is about three to four times larger than open demand orders, so only a small share of listed cards can sell on any given day.",
        "Executed trades are bounded by both sides of the book, so a doubling of demand orders does not double proceeds.",
        "Executed volume per day is the quantity that later limits how fast a residual inventory can be sold (next section)."])
    s += [PageBreak()]

    # ---- page 4 -------------------------------------------------------------------------------------------------------
    s += [P("4. Bot-farm Economics", "h1"),
          P("A multi-account strategy can look profitable on paper while most of its value is still locked in cards that have to be sold into a finite market. "
            "The analysis therefore reports three lenses side by side instead of one ROI figure."),
          table([["Lens", "What it represents"],
                 ["Realized value", "Cash actually withdrawn, after acquisition, setup and operating costs."],
                 ["Theoretical residual value", "Remaining live cards marked at the floor price, net of the marketplace fee."],
                 ["Liquidation-adjusted outcome", "Result after trying to sell the residual inventory during a finite liquidation window, at the depth the market can absorb."]],
                [CONTENT_W * 0.30, CONTENT_W * 0.70]),
          SP(1, 6), image(f_bf),
          P("Figure 5. (a) The three lenses for three illustrative entry routes; (b) liquidation-adjusted proceeds of 1,000 residual cards vs. the length of the liquidation window "
            "for three market depths. " + SYNTH, "caption"),
          P("Liquidation sensitivity", "h2"),
          P("Marking 1,000 cards at 1.00 gives a notional 1,000 (950 after a 5% fee). If the market absorbs 20 sales per day and the seller captures all of them, selling 900 cards takes "
            "at least 45 days — and only if demand stays stable. In this synthetic example a 45-day window in a market that absorbs 20 sales per day yields "
            f"about {at45:,.0f} of the {theo:,.0f} theoretical value: about 100 cards are still unsold and the seller has pushed its own price down. The engine continues the same economy "
            "after the horizon (a liquidation window), so competition, fees and expiry keep acting on the residual inventory."),
          SP(1, 4),
          table([["Liquidation assumption explored", "Effect on the outcome"],
                 ["Length of the liquidation window", "Too short a window leaves cards unsold; beyond the sell-down time more time adds nothing."],
                 ["Market depth (sales per day the market absorbs)", "Sets both the sell-down time and how far the seller pushes the price."],
                 ["Marketplace fee", "A fixed haircut on every executed sale."],
                 ["Price impact of the seller's own supply", "Selling into a thin book lowers the price of the next sale."],
                 ["Card lifetime during the window", "Cards that expire before they are sold are worth nothing."],
                 ["Competing sellers", "Other listings share the same demand, so the farm does not capture all executed trades."]],
                [CONTENT_W * 0.42, CONTENT_W * 0.58]),
          PageBreak()]

    # ---- page 5 -------------------------------------------------------------------------------------------------------
    s += [P("5. Financial Modeling", "h1"),
          P("The financial layer turns the simulated flows into three views that must reconcile with each other, rather than one profit number."),
          table([["View", "Question it answers"],
                 ["Accrual result", "What did the platform earn and spend in the period, regardless of when cash moved?"],
                 ["Cash flow", "When does money actually move? Drives the cumulative cash curve and the minimum cash position."],
                 ["Obligations and reserves", "What is owed to players (balances, prizes) and what reserve is required to stay solvent?"]],
                [CONTENT_W * 0.25, CONTENT_W * 0.75]),
          SP(1, 6), image(f_fin),
          P("Figure 6. Illustrative 24-month cash-flow model: (a) revenue and expense categories with net cash flow; (b) cumulative cash and its minimum. " + SYNTH, "caption"),
          P("Controls built into the financial engine", "h2")]
    s += bullets([
        "<b>Reconciliation identity:</b> cash + receivables − liabilities − unallocated amounts must equal the cumulative result; mismatches fail the run's checks.",
        "<b>Horizon coverage invariant:</b> aggregation must account for exactly the simulated number of days. After an independent review, regression tests cover horizons that are not "
        "multiples of 7 (for example 8, 9, 15, 729 and 730 days), so a trailing partial week cannot be dropped silently.",
        "<b>Capital need is a minimum, not a total:</b> the largest cumulative cash deficit and required reserves are reported separately from profit "
        f"(here the synthetic minimum is {abs(min_cum):,.0f} thousand notional units below zero, in month {min_month}).",
        "<b>Scenario honesty:</b> payment-channel fees, payout rates and marketing are scenario parameters; results are conditional on them."])
    s += [SP(1, 4), P("Examples of reconciliation checks", "h2"),
          table([["Check", "What it catches"],
                 ["Purchases counted once", "A purchase paid in one currency or channel must not be counted twice in revenue."],
                 ["Prize payouts equal engine payouts", "Money credited to players in the tournament module equals the expense and the liability in the financial layer."],
                 ["Balance-sheet style identity", "Cash, receivables, obligations and unallocated amounts must add up to the cumulative result."],
                 ["Every day of the horizon is covered", "No simulated day may be missing from the weekly or monthly financial tables."]],
                [CONTENT_W * 0.33, CONTENT_W * 0.67]),
          PageBreak()]

    # ---- page 6 -------------------------------------------------------------------------------------------------------
    s += [P("6. Sensitivity Analysis", "h1"),
          P("Many inputs of a game economy are assumptions rather than measurements. Sensitivity analysis shows which assumptions the conclusion actually depends on, "
            "so that verification effort goes where it matters."),
          image(f_tor),
          P("Figure 7. (a) Effect of moving one driver at a time to a low and a high test value (generic driver names); (b) the spread of an unchanged base case across seeds defines the noise band. " + SYNTH, "caption"),
          table([["Method element", "How it is used"],
                 ["One factor at a time", "Each driver is moved alone, with the same seed and engine, so the effect is attributable."],
                 ["Test ranges, not business values", "Low and high values (for example ×0.5 and ×1.5) are probes; they are not claims about acceptable or likely values."],
                 ["Noise threshold", "Effects inside the simulation-noise band (about 2 standard deviations across seeds) are not reported as influential."],
                 ["Conclusion flips", "The analysis flags drivers that change the sign of a result or the severity of a rule-based finding, not only its size."],
                 ["Criticality ≠ risk", "A parameter's influence is kept separate from the criticality of the business risk it touches."]],
                [CONTENT_W * 0.27, CONTENT_W * 0.73]),
          SP(1, 4), P("How the result is used", "h2")]
    s += bullets([
        "<b>Rank, then verify:</b> the longest bars are the assumptions to confirm with real data first; short bars can stay assumptions without changing the conclusion.",
        "<b>Compare with noise:</b> an effect is only meaningful when it exceeds the spread of the unchanged base case across seeds (panel b).",
        "<b>Stay conditional:</b> a driver that dominates under one set of assumptions need not dominate under another, so the analysis is repeated when the baseline changes."])
    s += [PageBreak()]

    # ---- page 7 -------------------------------------------------------------------------------------------------------
    rows = [["Run", "Seed", "Parameter hash", "Result digest", "Same as Run A?"]]
    for name, seed, r in results:
        rows.append([name, str(seed), r["params_hash"], r["digest"], "yes" if r["digest"] == base_digest else "no"])
    s += [P("7. Reproducibility", "h1"),
          P("Seed → simulation → digest → audit: every result can be traced to the exact inputs and software context that produced it, and a repeat run must produce the same digest."),
          image(f_pipe),
          P("Figure 8. Reproducibility pipeline (conceptual).", "caption"),
          table([["Recorded for every run", "Purpose"],
                 ["Engine and configuration version, parameter hash, seed", "Identify exactly what was simulated."],
                 ["Input-data provenance (synthetic or structured sports data)", "Separate modeled inputs from real data."],
                 ["Result digest (summary + tables, runtime excluded)", "Detect any change in the numbers, however small."],
                 ["Immutable configuration snapshot and append-only run ledger", "Keep the basis of a conclusion after scenarios change."],
                 ["File-level SHA-256 manifest of the audit kit", "Prove that the delivered documents match the verified calculations."]],
                [CONTENT_W * 0.55, CONTENT_W * 0.45]),
          P("Determinism demonstration", "h2"),
          P("The table below is produced by this script with a deliberately tiny seeded model (60 days, three named random streams). It is <b>not</b> the FIGHTEX engine; "
            "it only shows the mechanics: the same seed and parameters give the same digest, while a different seed or a single changed parameter gives a different one."),
          table(rows, [CONTENT_W * 0.30, CONTENT_W * 0.09, CONTENT_W * 0.22, CONTENT_W * 0.22, CONTENT_W * 0.17], mono_cols=(2, 3)),
          P(SYNTH + " Digests are computed from the toy model at build time.", "caption"),
          P("Scope and limitations", "h2"),
          P("Simulation outputs are conditional scenarios, not financial forecasts. Independent review findings are tracked and re-validated; corrected calculations ship as a new, separately "
            "identified audit kit rather than overwriting an accepted one. This document is not a security certification.", "body")]

    doc.build(s)


def main() -> int:
    if not DATA.exists():
        print("data/ is missing: run generate_synthetic_data.py first", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp))
    print(f"written {OUT} ({OUT.stat().st_size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
