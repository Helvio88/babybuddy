# -*- coding: utf-8 -*-
"""
Plotly chart builders for Dashboard NG (live data only).

Dark-theme styling matches Baby Buddy reports (see reports.utils).
HTML goes in the page body; JS is deferred until graph.js loads.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objs as go
import plotly.offline as plotly

from reports.utils import default_graph_layout_options, split_graph_output


# Bright accents that read well on Baby Buddy's dark cards
FEED = "#37abe9"       # baby buddy primary blue
DIAPER = "#f0ad4e"     # warm amber
GROWTH = "#5cb85c"     # green
PUMP = "#b39ddb"       # soft purple
TEMP = "#ff6b6b"       # coral red
OK = "#5cb85c"
MUTED = "rgba(255,255,255,0.45)"
GRID = "rgba(255,255,255,0.12)"
AXIS = "rgba(255,255,255,0.55)"
PAPER = "rgb(52, 58, 64)"
PIE_PALETTE = [
    "#37abe9",
    "#f0ad4e",
    "#5cb85c",
    "#b39ddb",
    "#ff6b6b",
    "#4dd0e1",
    "#ffd54f",
    "#81c784",
]


def _layout(height: int = 300, dual_y: bool = False, y_title: str = "", y2_title: str = "") -> dict:
    """Dark layout based on Baby Buddy report defaults, sized for dashboard cards."""
    base = default_graph_layout_options()
    layout = {
        **base,
        "height": height,
        "autosize": True,
        "margin": dict(l=48, r=28 if not dual_y else 52, t=28, b=48),
        "paper_bgcolor": PAPER,
        "plot_bgcolor": PAPER,
        "font": {
            **base["font"],
            "size": 12,
            "color": "rgba(255, 255, 255, 0.92)",
        },
        "xaxis": {
            **base.get("xaxis", {}),
            "showgrid": False,
            "zeroline": False,
            "color": AXIS,
            "tickfont": {"color": AXIS, "size": 11},
            "title": "",
        },
        "yaxis": {
            **base.get("yaxis", {}),
            "showgrid": True,
            "gridcolor": GRID,
            "zeroline": False,
            "color": AXIS,
            "tickfont": {"color": AXIS, "size": 11},
            "title": y_title,
            "titlefont": {"color": AXIS, "size": 12},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.05,
            "x": 0,
            "font": {"color": "rgba(255,255,255,0.85)", "size": 11},
            "bgcolor": "rgba(0,0,0,0)",
        },
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": "rgb(33, 37, 41)",
            "bordercolor": "rgba(255,255,255,0.2)",
            "font": {"color": "#fff", "size": 12},
        },
    }
    if dual_y:
        layout["yaxis2"] = {
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "zeroline": False,
            "color": AXIS,
            "tickfont": {"color": AXIS, "size": 11},
            "title": y2_title,
            "titlefont": {"color": AXIS, "size": 12},
        }
    return layout


def _to_parts(fig: go.Figure) -> Tuple[str, str]:
    fig.update_layout(autosize=True)
    output = plotly.plot(
        fig,
        output_type="div",
        include_plotlyjs=False,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
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
                marker=dict(color=color, line=dict(width=0)),
                hovertemplate="%{x}<br>%{y}<extra></extra>",
            )
        ],
        layout=_layout(height=300),
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
                marker=dict(color=a_color, line=dict(width=0)),
            ),
            go.Scatter(
                x=labels,
                y=[s["value"] for s in b_series] if b_series else [],
                name=b_name,
                mode="lines+markers",
                line=dict(color=b_color, width=2.5),
                marker=dict(size=6, color=b_color),
                yaxis="y2",
            ),
        ],
        layout=_layout(height=300, dual_y=True, y_title=a_name, y2_title=b_name),
    )
    return _to_parts(fig)


def pie_breakdown(
    items: List[Dict[str, Any]], colors: Optional[List[str]] = None
) -> Tuple[str, str]:
    if not items:
        return _empty()
    palette = colors or PIE_PALETTE
    layout = _layout(height=300)
    layout["margin"] = dict(l=16, r=16, t=16, b=16)
    layout["showlegend"] = False
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[i["name"] for i in items],
                values=[i["value"] for i in items],
                hole=0.48,
                marker=dict(
                    colors=palette[: len(items)],
                    line=dict(color=PAPER, width=2),
                ),
                textinfo="label+percent",
                textfont=dict(color="#fff", size=12),
                hoverinfo="label+value+percent",
            )
        ],
        layout=layout,
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
                marker=dict(color=color, line=dict(width=0)),
                hovertemplate="%{x}:00<br>%{y}<extra></extra>",
            )
        ],
        layout=_layout(height=260),
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
                marker=dict(color=FEED, line=dict(width=0)),
            )
        ],
        layout=_layout(height=260),
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
                line=dict(color=GROWTH, width=2.5),
                marker=dict(size=7, color=GROWTH, line=dict(color=PAPER, width=1)),
                fill="tozeroy",
                fillcolor="rgba(92, 184, 92, 0.15)",
                name="Weight (kg)",
            )
        ],
        layout=_layout(height=320),
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
                line=dict(color=FEED, width=2.5),
                marker=dict(size=7, color=FEED),
            )
        )
    if head:
        data.append(
            go.Scatter(
                x=[s["label"] for s in head],
                y=[s["cm"] for s in head],
                mode="lines+markers",
                name="Head (cm)",
                line=dict(color=PUMP, width=2.5),
                marker=dict(size=7, color=PUMP),
            )
        )
    if not data:
        return _empty()
    fig = go.Figure(data=data, layout=_layout(height=320))
    return _to_parts(fig)


def pump_bars(series: List[Dict[str, Any]]) -> Tuple[str, str]:
    if not series:
        return _empty()
    fig = go.Figure(
        data=[
            go.Bar(
                x=[s["label"] for s in series],
                y=[s["value"] for s in series],
                marker=dict(color=PUMP, line=dict(width=0)),
                name="ml",
            )
        ],
        layout=_layout(height=300),
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
                line=dict(color=TEMP, width=2.5),
                marker=dict(size=7, color=TEMP),
                name="°C",
            )
        ],
        layout=_layout(height=280),
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
            GROWTH,
        ),
        "chart_diaper_kinds": pie_breakdown(ctx.get("diaper_kinds") or []),
        "chart_diaper_colors": pie_breakdown(
            ctx.get("diaper_colors") or [],
            ["#ffd54f", "#81c784", "#a1887f", "#90a4ae", MUTED],
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
