"""Render report charts without opening GUI windows in the report worker."""
from pathlib import Path
from math import isfinite

from matplotlib.figure import Figure as Plot
from pylatex import Figure, NoEscape

from .styles import CHART_COLOR, FAIL_COLOR


def number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if isfinite(value) and value >= 0 else None


def bar_chart(directory, name, panels, caption, threshold=False):
    if directory is None:
        return ""
    plot = Plot(figsize=(7.2, 4.0) if threshold else (7.2, 3.4), layout="constrained")
    axes = plot.subplots(1, len(panels), squeeze=False)[0]
    for axis, (unit, series) in zip(axes, panels):
        values = [number(value) for value in series.values()]
        axis.set_xticks(range(len(values)), [label.replace(" ", "\n", 1) if threshold else label for label in series], fontsize=10)
        top = max([1.0 if threshold else 0.01] + [v for v in values if v is not None])
        axis.set_ylim(0, top * 1.25)
        if not any(value is not None for value in values):
            axis.set_yticks([])
        axis.set_ylabel(unit)
        axis.grid(axis="y", alpha=0.2)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        for i, v in enumerate(values):
            if v is not None:
                axis.bar(i, v, width=0.58, color=FAIL_COLOR if threshold and v > 1 else CHART_COLOR)
            axis.text(i, (v or 0) + top * 0.025, "N/A" if v is None else f"{v:.3g}", ha="center")
        if threshold:
            axis.axhline(1, color=FAIL_COLOR, linestyle="--", linewidth=1.4)
    path = Path(directory) / (name + ".png")
    plot.savefig(path, dpi=170)
    figure = Figure(position="H")
    figure.add_image(NoEscape(path.as_posix()), width=NoEscape(r"0.94\linewidth"))
    figure.add_caption(caption)
    return figure.dumps()
