"""
Generate example data-visualization charts for CSCL activities.

Uses matplotlib to produce self-contained base64 PNG images that can be
embedded directly in the activity output (student_worksheet / student_slides).
"""
import base64
import io
import logging
import os
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_plt = None
HAS_MATPLOTLIB = None

def _get_plt():
    """Lazy-load matplotlib to avoid startup memory/time cost."""
    global _plt, HAS_MATPLOTLIB
    if HAS_MATPLOTLIB is not None:
        return _plt
    try:
        os.environ.setdefault("MPLBACKEND", "Agg")
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        _plt = plt
        HAS_MATPLOTLIB = True
    except Exception:
        _plt = None
        HAS_MATPLOTLIB = False
        logger.warning("matplotlib not available – chart generation disabled")
    return _plt


def _fig_to_base64(fig) -> str:
    plt = _get_plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _make_bar_chart(title: str, labels: List[str], values: List[float],
                    ylabel: str = "Value", color: str = "#3b82f6",
                    bad_version: bool = False) -> str:
    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(labels, values, color=color, edgecolor="white", width=0.6)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if bad_version:
        ax.set_ylim(min(values) * 0.9, max(values) * 1.05)
        ax.set_title(title + " (truncated axis)", fontsize=12, fontweight="bold", pad=10)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    return _fig_to_base64(fig)


def _make_line_chart(title: str, x: List, y_series: Dict[str, List[float]],
                     xlabel: str = "X", ylabel: str = "Y") -> str:
    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = ["#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6"]
    for i, (name, ys) in enumerate(y_series.items()):
        ax.plot(x, ys, marker="o", markersize=4, linewidth=2,
                color=colors[i % len(colors)], label=name)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_base64(fig)


def _make_pie_chart(title: str, labels: List[str], sizes: List[float],
                    explode_biggest: bool = False) -> str:
    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = ["#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
              "#ec4899", "#14b8a6", "#f97316"]
    explode = [0] * len(sizes)
    if explode_biggest:
        explode[sizes.index(max(sizes))] = 0.08
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90,
           colors=colors[:len(sizes)], explode=explode,
           textprops={"fontsize": 9})
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    return _fig_to_base64(fig)


_EXAMPLE_CHART_SETS = {
    "data_visualization": lambda topic: [
        {
            "chart_id": "good_bar",
            "title": f"Chart A – Clear Bar Chart ({topic})",
            "description": "A well-designed bar chart with zero baseline, clear labels, and appropriate scale.",
            "base64": _make_bar_chart(
                f"Student Performance by Group", 
                ["Group A", "Group B", "Group C", "Group D", "Group E"],
                [78, 85, 62, 91, 74], ylabel="Score (%)", color="#22c55e"),
            "chart_type": "bar",
            "purpose": "example_good",
        },
        {
            "chart_id": "bad_bar",
            "title": f"Chart B – Misleading Bar Chart ({topic})",
            "description": "The same data but with a truncated y-axis starting at 60, making small differences look dramatic.",
            "base64": _make_bar_chart(
                f"Student Performance by Group",
                ["Group A", "Group B", "Group C", "Group D", "Group E"],
                [78, 85, 62, 91, 74], ylabel="Score (%)", color="#ef4444",
                bad_version=True),
            "chart_type": "bar",
            "purpose": "example_bad",
        },
    ],
    "general": lambda topic: [
        {
            "chart_id": "overview_bar",
            "title": f"Sample Data Overview – {topic}",
            "description": "A sample bar chart generated from example data to support the collaborative activity.",
            "base64": _make_bar_chart(
                f"Comparison: {topic[:40]}",
                ["Category A", "Category B", "Category C", "Category D"],
                [random.randint(40, 95) for _ in range(4)],
                ylabel="Metric", color="#3b82f6"),
            "chart_type": "bar",
            "purpose": "activity_data",
        },
    ],
}

_VIZ_KEYWORDS = [
    "visualization", "visualisation", "chart", "graph", "plot",
    "data", "statistic", "infographic", "diagram",
]


def _pick_chart_set(topic: str, task_type: str) -> str:
    t = (topic or "").lower()
    if any(kw in t for kw in _VIZ_KEYWORDS):
        return "data_visualization"
    return "general"


def generate_activity_charts(
    spec: Dict[str, Any],
    planner_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    _get_plt()
    if not HAS_MATPLOTLIB:
        logger.info("matplotlib unavailable, skipping chart generation")
        return []

    cc = spec.get("course_context") or {}
    topic = cc.get("topic") or cc.get("subject") or "Collaborative Activity"
    task_type = (spec.get("task_requirements") or {}).get("task_type", "")

    chart_set_key = _pick_chart_set(topic, task_type)
    factory = _EXAMPLE_CHART_SETS.get(chart_set_key, _EXAMPLE_CHART_SETS["general"])

    try:
        charts = factory(topic)
        logger.info("Generated %d charts (set=%s) for topic '%s'", len(charts), chart_set_key, topic[:60])
        return charts
    except Exception:
        logger.exception("Chart generation failed")
        return []
