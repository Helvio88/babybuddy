# -*- coding: utf-8 -*-
"""
Plotly chart builders for Dashboard NG (live data only).
Independent of existing reports.graphs modules.

Matches Baby Buddy reports: HTML goes in the page body; JS is deferred until
after babybuddy/js/graph.js (Plotly) loads, so Plotly is defined.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objs as go
import plotly.offline as plotly

from reports.utils import split_graph_output


PRIMARY = "#2f6f6a"
FEED = "#2f6f6a"
DIAPER = "#8a6a3d"
GROWTH = "#3d5a80"
PUMP = "#6b5b95"
OK = "#3d7a4a"
MUTED = "#948c84"


def _layout(title: str = "", height: int = 280) -> go.Layout:
    return go.Layout(
        title=None,
        height=height,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, sans-serif", size=12, color="#1c1a17"),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#e2ddd6", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )


def _to_parts(fig: go.Figure) -> Tuple[str, str]:
    """Return (html_div, script_tags) so Plotly JS can load first."""
    output = plotly.plot(
        fig,
        output_type="div",
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )
    return split_graph_output(output)


def _empty() -> Tuple[str, str]:
    return "", ""


def daily_bar(
    series: List[Dict[str, Any]], color: str = FEED, name: str = "Count"
) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[s["label"] for s in series],
                y=[s["value"] for s in series],
                name=name,
                marker=dict(color=color),
            )
        ],
        layout=_layout(),
    )
    return _to_parts(fig)


def dual_daily(
    a_series: List[Dict[str, Any]],
    b_series: List[Dict[str, Any]],
    a_name: str,
    b_name: str,
    a_color: str = FEED,
    b_color: str = GROWTH,
) -> Tuple[str, str]:
    if not a_series:
        return _empty()
    labels = [s["label"] for s in a_series]
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=[s["value"] for s in a_series],
                name=a_name,
                marker=dict(color=a_color),
            ),
            go.Scatter(
                x=labels,
                y=[s["value"] for s in b_series] if b_series else [],
                name=b_name,
                mode="lines+markers",
                line=dict(color=b_color, width=2),
                yaxis="y2",
            ),
        ],
        layout=go.Layout(
            height=280,
            margin=dict(l=40, r=50, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12, color="#1c1a17"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#e2ddd6", title=a_name),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title=b_name),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            hovermode="x unified",
        ),
    )
    return _to_parts(fig)


def pie_breakdown(
    items: List[Dict[str, Any]], colors: Optional[List[str]] = None
) -> Tuple[str, str]:
    if not items:
        return _empty()
    palette = colors or [PRIMARY, DIAPER, GROWTH, PUMP, OK, MUTED]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[i["name"] for i in items],
                values=[i["value"] for i in items],
                hole=0.45,
                marker=dict(colors=palette[: len(items)]),
                textinfo="label+percent",
            )
        ],
        layout=go.Layout(
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12, color="#1c1a17"),
            showlegend=False,
        ),
    )
    return _to_parts(fig)


def hourly_bars(
    series: List[Dict[str, Any]], color: str = FEED
) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[s["label"] for s in series],
                y=[s["count"] for s in series],
                marker=dict(color=color),
            )
        ],
        layout=_layout(height=240),
    )
    return _to_parts(fig)


def interval_bars(series: List[Dict[str, Any]]) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[s["label"] for s in series],
                y=[s["count"] for s in series],
                marker=dict(color=PRIMARY),
            )
        ],
        layout=_layout(height=240),
    )
    return _to_parts(fig)


def weight_line(series: List[Dict[str, Any]]) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Scatter(
                x=[s["label"] for s in series],
                y=[s["kg"] for s in series],
                mode="lines+markers",
                line=dict(color=GROWTH, width=2),
                marker=dict(size=6),
                name="Weight (kg)",
            )
        ],
        layout=_layout(height=300),
    )
    return _to_parts(fig)


def growth_multi(
    height: List[Dict[str, Any]], head: List[Dict[str, Any]]
) -> Tuple[str, str]:
    data = []
    if height:
        data.append(
            go.Scatter(
                x=[s["label"] for s in height],
                y=[s["cm"] for s in height],
                mode="lines+markers",
                name="Length (cm)",
                line=dict(color=PRIMARY, width=2),
            )
        )
    if head:
        data.append(
            go.Scatter(
                x=[s["label"] for s in head],
                y=[s["cm"] for s in head],
                mode="lines+markers",
                name="Head (cm)",
                line=dict(color=PUMP, width=2),
            )
        )
    if not data:
        return _empty()
    fig = go.Figure(data=data, layout=_layout(height=300))
    return _to_parts(fig)


def pump_bars(series: List[Dict[str, Any]]) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[s["label"] for s in series],
                y=[s["value"] for s in series],
                marker=dict(color=PUMP),
                name="ml",
            )
        ],
        layout=_layout(),
    )
    return _to_parts(fig)


def temp_line(series: List[Dict[str, Any]]) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Scatter(
                x=[s["label"] for s in series],
                y=[s["c"] for s in series],
                mode="lines+markers",
                line=dict(color="#a63d40", width=2),
                name="°C",
            )
        ],
        layout=_layout(height=260),
    )
    return _to_parts(fig)


def build_all_charts(ctx: Dict[str, Any]) -> Dict[str, str]:
    """
    Return chart HTML keys plus a single charts_js blob for the footer.

    Template must load graph.js first, then {{ charts_js|safe }}.
    """
    parts = {
        "chart_feed_daily": daily_bar(ctx.get("feed_daily") or [], FEED, "Feeds"),
        "chart_feed_dual": dual_daily(
            ctx.get("feed_daily") or [],
            ctx.get("feed_minutes_daily") or [],
            "Feeds",
            "Minutes",
            FEED,
            GROWTH,
        ),
        "chart_intervals": interval_bars(ctx.get("intervals") or []),
        "chart_feed_hours": hourly_bars(ctx.get("feed_hours") or [], FEED),
        "chart_methods": pie_breakdown(ctx.get("methods") or []),
        "chart_diaper_dual": dual_daily(
            ctx.get("wet_daily") or [],
            ctx.get("solid_daily") or [],
            "Wet",
            "Solid",
            DIAPER,
            OK,
        ),
        "chart_diaper_kinds": pie_breakdown(ctx.get("diaper_kinds") or []),
        "chart_diaper_colors": pie_breakdown(
            ctx.get("diaper_colors") or [],
            ["#d4a017", "#6b8e23", "#8b5a2b", "#4a4a4a", MUTED],
        ),
        "chart_diaper_hours": hourly_bars(ctx.get("diaper_hours") or [], DIAPER),
        "chart_weight": weight_line(ctx.get("weight_series") or []),
        "chart_growth": growth_multi(
            ctx.get("height_series") or [], ctx.get("head_series") or []
        ),
        "chart_pump": pump_bars(ctx.get("pump_daily") or []),
        "chart_temp": temp_line(ctx.get("temp_series") or []),
    }

    out: Dict[str, str] = {}
    js_chunks: List[str] = []
    for key, (html, js) in parts.items():
        out[key] = html
        if js:
            js_chunks.append(js)
    out["charts_js"] = "\n".join(js_chunks)
    return out
