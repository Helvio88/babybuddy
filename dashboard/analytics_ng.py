# -*- coding: utf-8 -*-
"""
Live analytics helpers for the Dashboard NG page.

Reads directly from Django ORM models — no external MCP or snapshot files.
Does not modify any existing dashboard card/report functions.
"""
from __future__ import annotations

import datetime
import statistics
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from django.utils import timezone

from core import models


RANGE_CHOICES = ("7d", "14d", "30d", "all")


def parse_range(key: Optional[str]) -> str:
    if key in RANGE_CHOICES:
        return key
    return "14d"


def range_bounds(key: str, as_of=None) -> Tuple[datetime.datetime, datetime.datetime, str, int]:
    """
    Return (from_dt, to_dt, label, day_count) for the selected window.
    from_dt is timezone-aware start of first day (or very early for "all").
    """
    as_of = as_of or timezone.localtime()
    if key == "all":
        start = timezone.make_aware(
            datetime.datetime(2000, 1, 1, 0, 0, 0),
            timezone.get_current_timezone(),
        )
        days = max(1, (as_of.date() - start.date()).days + 1)
        return start, as_of, "All time", days

    days = {"7d": 7, "14d": 14, "30d": 30}.get(key, 14)
    start_date = as_of.date() - datetime.timedelta(days=days - 1)
    start = timezone.make_aware(
        datetime.datetime.combine(start_date, datetime.time.min),
        timezone.get_current_timezone(),
    )
    return start, as_of, f"Last {days} days", days


def _median(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return float(statistics.median(values))


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def _to_float(value: Any) -> float:
    """Coerce Measurement / Decimal / numeric fields to float."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    for attr in ("value", "kg", "cm", "c", "mm", "g"):
        if hasattr(value, attr):
            try:
                return float(getattr(value, attr))
            except (TypeError, ValueError):
                continue
    return float(str(value).split()[0])


def feed_minutes(feeding: models.Feeding) -> float:
    if feeding.duration:
        return feeding.duration.total_seconds() / 60.0
    if feeding.start and feeding.end:
        return max(0.0, (feeding.end - feeding.start).total_seconds() / 60.0)
    return 0.0


def feeding_intervals_minutes(feedings: Sequence[models.Feeding]) -> List[float]:
    ordered = sorted(feedings, key=lambda f: f.start)
    out: List[float] = []
    for i in range(1, len(ordered)):
        mins = (ordered[i].start - ordered[i - 1].start).total_seconds() / 60.0
        if 0 < mins < 24 * 60:
            out.append(mins)
    return out


def daily_counts(
    timestamps: Iterable[datetime.datetime],
    from_dt: datetime.datetime,
    to_dt: datetime.datetime,
) -> List[Dict[str, Any]]:
    """Return one entry per calendar day in range with count."""
    start_date = timezone.localtime(from_dt).date()
    end_date = timezone.localtime(to_dt).date()
    counts: Dict[datetime.date, int] = {}
    cursor = start_date
    while cursor <= end_date:
        counts[cursor] = 0
        cursor += datetime.timedelta(days=1)
    for ts in timestamps:
        local = timezone.localtime(ts).date()
        if local in counts:
            counts[local] += 1
    return [
        {"date": d.isoformat(), "label": d.strftime("%b %d"), "value": counts[d]}
        for d in sorted(counts)
    ]


def daily_sums(
    pairs: Iterable[Tuple[datetime.datetime, float]],
    from_dt: datetime.datetime,
    to_dt: datetime.datetime,
) -> List[Dict[str, Any]]:
    start_date = timezone.localtime(from_dt).date()
    end_date = timezone.localtime(to_dt).date()
    totals: Dict[datetime.date, float] = {}
    cursor = start_date
    while cursor <= end_date:
        totals[cursor] = 0.0
        cursor += datetime.timedelta(days=1)
    for ts, value in pairs:
        local = timezone.localtime(ts).date()
        if local in totals:
            totals[local] += value
    return [
        {"date": d.isoformat(), "label": d.strftime("%b %d"), "value": totals[d]}
        for d in sorted(totals)
    ]


def weight_daily_averages(weights: Sequence[models.Weight]) -> List[Dict[str, Any]]:
    """One point per calendar day — mean of all weigh-ins that day."""
    by_day: Dict[datetime.date, List[float]] = defaultdict(list)
    for w in weights:
        by_day[w.date].append(_to_float(w.weight))
    series: List[Dict[str, Any]] = []
    for day in sorted(by_day):
        vals = by_day[day]
        series.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%b %d"),
                "kg": sum(vals) / len(vals),
                "n": len(vals),
            }
        )
    return series


def hourly_histogram(timestamps: Iterable[datetime.datetime]) -> List[Dict[str, Any]]:
    hours = [0] * 24
    for ts in timestamps:
        hours[timezone.localtime(ts).hour] += 1
    return [{"hour": h, "label": f"{h:02d}", "count": hours[h]} for h in range(24)]


def interval_histogram(
    intervals: Sequence[float], bin_minutes: int = 30
) -> List[Dict[str, Any]]:
    bins: Dict[int, int] = defaultdict(int)
    for mins in intervals:
        bucket = int(mins // bin_minutes) * bin_minutes
        bins[bucket] += 1
    return [
        {
            "label": f"{bucket}-{bucket + bin_minutes}m",
            "count": bins[bucket],
            "sort": bucket,
        }
        for bucket in sorted(bins)
    ]


def weight_gain_per_day(weights: Sequence[models.Weight], lookback_days: int = 14):
    if len(weights) < 2:
        return None
    ordered = sorted(weights, key=lambda w: w.date)
    last = ordered[-1]
    target = last.date - datetime.timedelta(days=lookback_days)
    earlier = ordered[0]
    for w in ordered:
        if w.date <= target:
            earlier = w
    days = (last.date - earlier.date).days
    if days <= 0:
        return None
    gain_kg = _to_float(last.weight) - _to_float(earlier.weight)
    return {
        "grams_per_day": (gain_kg * 1000.0) / days,
        "from": earlier,
        "to": last,
        "days": days,
    }


def night_feed_share(feedings: Sequence[models.Feeding]) -> float:
    if not feedings:
        return 0.0
    night = 0
    for f in feedings:
        hour = timezone.localtime(f.start).hour
        if hour >= 22 or hour < 6:
            night += 1
    return night / len(feedings)


def build_insights(child: models.Child, range_key: str) -> List[Dict[str, str]]:
    from_dt, to_dt, _label, days = range_bounds(range_key)
    feeds = list(
        models.Feeding.objects.filter(child=child, start__gte=from_dt, start__lte=to_dt)
    )
    changes = list(
        models.DiaperChange.objects.filter(
            child=child, time__gte=from_dt, time__lte=to_dt
        )
    )
    weights = list(models.Weight.objects.filter(child=child).order_by("date"))
    insights: List[Dict[str, str]] = []

    feed_days = daily_counts([f.start for f in feeds], from_dt, to_dt)
    daily_feed_values = [d["value"] for d in feed_days if d["value"] > 0]
    avg_feeds = _mean(daily_feed_values)
    intervals = feeding_intervals_minutes(feeds)
    med_interval = _median(intervals)
    wet_days = daily_counts([c.time for c in changes if c.wet], from_dt, to_dt)
    avg_wet = _mean([d["value"] for d in wet_days if d["value"] > 0])
    solid_days = daily_counts([c.time for c in changes if c.solid], from_dt, to_dt)
    avg_solid = _mean([d["value"] for d in solid_days])
    gain = weight_gain_per_day(weights, 14)
    night_share = night_feed_share(feeds)

    if avg_feeds > 0:
        if 8 <= avg_feeds <= 14:
            body = (
                "Right in the common range for an exclusively breastfed infant. "
                "Cluster feeds still count."
            )
            tone = "info"
        elif avg_feeds < 8:
            body = (
                "Fewer feeds than typical for exclusive nursing — worth confirming "
                "baby is content and gaining."
            )
            tone = "warn"
        else:
            body = (
                "High feed frequency. Normal during growth spurts and cluster "
                "periods, especially evenings."
            )
            tone = "info"
        insights.append(
            {
                "id": "feeds-per-day",
                "tone": tone,
                "title": f"{avg_feeds:.1f} feeds / day on average",
                "body": body,
            }
        )

    if med_interval is not None:
        tone = "warn" if med_interval < 90 else "ok"
        if med_interval < 90:
            body = (
                "Feeds are close together. Common with cluster feeding; watch for "
                "adequate wet diapers and weight gain."
            )
        elif med_interval <= 180:
            body = (
                "Intervals look steady. A predictable rhythm helps both parents "
                "anticipate the next session."
            )
        else:
            body = (
                "Longer gaps between feeds. Fine if weight gain and diaper output "
                "stay strong."
            )
        insights.append(
            {
                "id": "interval",
                "tone": tone,
                "title": f"Median time between feeds: {int(round(med_interval))} min",
                "body": body,
            }
        )

    if avg_wet > 0:
        tone = "ok" if avg_wet >= 6 else "warn"
        body = (
            "Hydration markers look solid. Six or more wet diapers is a classic "
            "good sign for intake."
            if avg_wet >= 6
            else (
                "Wet diaper count is on the low side of typical. Track over the "
                "next day and compare with feeds."
            )
        )
        insights.append(
            {
                "id": "wet-diapers",
                "tone": tone,
                "title": f"{avg_wet:.1f} wet diapers / day",
                "body": body,
            }
        )

    if sum(d["value"] for d in solid_days) > 0:
        body = (
            "Active stooling. Yellow soft stools are typical for breastfed babies."
            if avg_solid >= 1
            else (
                "Stools are spaced out. Breastfed babies can go longer between "
                "poops after the early weeks if soft when they come."
            )
        )
        insights.append(
            {
                "id": "stool-pattern",
                "tone": "info",
                "title": f"{avg_solid:.1f} stools / day",
                "body": body,
            }
        )

    if gain:
        g = gain["grams_per_day"]
        if g >= 20:
            tone, body = (
                "ok",
                "Strong gain — growth is on a healthy trajectory for this age.",
            )
        elif g >= 10:
            tone, body = (
                "ok",
                "Steady gain. Pediatric curves often settle around 15–30 g/day "
                "in the first months.",
            )
        elif g >= 0:
            tone, body = (
                "info",
                "Slow gain recently. Compare scale conditions (diaper on/off) "
                "and check overall trend.",
            )
        else:
            tone, body = (
                "warn",
                "Recent weight dipped. Day-to-day scale noise is common — look "
                "at the multi-week curve.",
            )
        sign = "+" if g >= 0 else ""
        insights.append(
            {
                "id": "weight-gain",
                "tone": tone,
                "title": f"Weight trend: {sign}{g:.0f} g/day (last {gain['days']}d)",
                "body": body,
            }
        )

    if feeds:
        body = (
            "Nights are still busy. Tag-team shifts and side-lying nursing can "
            "protect sleep."
            if night_share > 0.35
            else (
                "Night load is moderate. Keeping the room dark and boring for "
                "night feeds helps protect circadian cues."
            )
        )
        insights.append(
            {
                "id": "night-feeds",
                "tone": "info",
                "title": f"{int(round(night_share * 100))}% of feeds are overnight (10pm–6am)",
                "body": body,
            }
        )

    vit_d = 0
    for f in feeds:
        try:
            if f.tags.filter(name__icontains="Vitamin D").exists():
                vit_d += 1
        except Exception:
            pass
    if vit_d:
        insights.append(
            {
                "id": "vitd",
                "tone": "ok",
                "title": f"Vitamin D tagged on {vit_d} feed{'s' if vit_d != 1 else ''} in range",
                "body": (
                    "Nice consistency — AAP recommends 400 IU vitamin D daily for "
                    "exclusively breastfed infants."
                ),
            }
        )

    sleep_count = models.Sleep.objects.filter(
        child=child, start__gte=from_dt, start__lte=to_dt
    ).count()
    if sleep_count == 0:
        insights.append(
            {
                "id": "sleep-gap",
                "tone": "info",
                "title": "No sleep sessions in this window",
                "body": (
                    "Adding naps and night sleep unlocks wake-window and "
                    "night-stretch insights here."
                ),
            }
        )
    else:
        insights.append(
            {
                "id": "sleep-count",
                "tone": "ok",
                "title": f"{sleep_count} sleep sessions logged in range",
                "body": "Sleep tracking is active — keep logging to spot nap patterns.",
            }
        )

    return insights


def build_dashboard_context(child: models.Child, range_key: str) -> Dict[str, Any]:
    """
    Assemble all live metrics for Dashboard NG from the database.
    """
    range_key = parse_range(range_key)
    from_dt, to_dt, range_label, days = range_bounds(range_key)

    feeds = list(
        models.Feeding.objects.filter(child=child, start__gte=from_dt, start__lte=to_dt)
        .prefetch_related("tags")
        .order_by("-start")
    )
    changes = list(
        models.DiaperChange.objects.filter(
            child=child, time__gte=from_dt, time__lte=to_dt
        ).order_by("-time")
    )
    pumps = list(
        models.Pumping.objects.filter(
            child=child, start__gte=from_dt, start__lte=to_dt
        ).order_by("-start")
    )
    weights = list(models.Weight.objects.filter(child=child).order_by("date"))
    heights = list(models.Height.objects.filter(child=child).order_by("date"))
    heads = list(
        models.HeadCircumference.objects.filter(child=child).order_by("date")
    )
    temps = list(models.Temperature.objects.filter(child=child).order_by("time"))
    notes = list(models.Note.objects.filter(child=child).order_by("-time")[:12])
    sleeps = list(
        models.Sleep.objects.filter(
            child=child, start__gte=from_dt, start__lte=to_dt
        ).order_by("-start")
    )

    intervals = feeding_intervals_minutes(feeds)
    total_feed_min = sum(feed_minutes(f) for f in feeds)
    wet_count = sum(1 for c in changes if c.wet)
    solid_count = sum(1 for c in changes if c.solid)
    gain = weight_gain_per_day(weights, 14)
    last_feed = feeds[0] if feeds else models.Feeding.objects.filter(child=child).first()
    last_change = (
        changes[0]
        if changes
        else models.DiaperChange.objects.filter(child=child).first()
    )
    latest_weight = weights[-1] if weights else None
    last_height = heights[-1] if heights else None
    last_head = heads[-1] if heads else None
    last_temp = temps[-1] if temps else None

    method_counts = Counter(f.method for f in feeds)
    diaper_kinds = Counter()
    for c in changes:
        if c.wet and c.solid:
            diaper_kinds["Wet + solid"] += 1
        elif c.wet:
            diaper_kinds["Wet only"] += 1
        elif c.solid:
            diaper_kinds["Solid only"] += 1
        else:
            diaper_kinds["Other"] += 1
    color_counts = Counter(
        (c.color or "unspecified").lower() for c in changes if c.solid
    )

    feed_daily = daily_counts([f.start for f in feeds], from_dt, to_dt)
    feed_minutes_daily = daily_sums(
        [(f.start, feed_minutes(f)) for f in feeds], from_dt, to_dt
    )
    wet_daily = daily_counts([c.time for c in changes if c.wet], from_dt, to_dt)
    solid_daily = daily_counts([c.time for c in changes if c.solid], from_dt, to_dt)
    pump_daily = daily_sums(
        [(p.start, float(p.amount or 0)) for p in pumps], from_dt, to_dt
    )

    recent: List[Dict[str, Any]] = []
    for f in feeds[:8]:
        recent.append(
            {
                "kind": "Feed",
                "title": f.get_method_display()
                if hasattr(f, "get_method_display")
                else f.method,
                "when": f.start,
                "detail": f"{int(round(feed_minutes(f)))} min"
                + (f" · {f.amount:g}" if f.amount else ""),
            }
        )
    for c in changes[:8]:
        kind = (
            "Wet + solid"
            if c.wet and c.solid
            else "Wet"
            if c.wet
            else "Solid"
            if c.solid
            else "Change"
        )
        recent.append(
            {
                "kind": "Diaper",
                "title": kind,
                "when": c.time,
                "detail": c.color or "",
            }
        )
    recent.sort(key=lambda x: x["when"], reverse=True)
    recent = recent[:12]

    lifetime_feeds = models.Feeding.objects.filter(child=child).count()
    lifetime_changes = models.DiaperChange.objects.filter(child=child).count()

    return {
        "range_key": range_key,
        "range_label": range_label,
        "range_choices": [
            ("7d", "7d"),
            ("14d", "14d"),
            ("30d", "30d"),
            ("all", "All"),
        ],
        "from_dt": from_dt,
        "to_dt": to_dt,
        "days": days,
        "feeds": feeds,
        "changes": changes,
        "pumps": pumps,
        "sleeps": sleeps,
        "notes": notes,
        "feed_count": len(feeds),
        "feeds_per_day": len(feeds) / days,
        "avg_feed_minutes": _mean([feed_minutes(f) for f in feeds]),
        "total_feed_hours": total_feed_min / 60.0,
        "median_interval": _median(intervals),
        "wet_count": wet_count,
        "solid_count": solid_count,
        "changes_per_day": len(changes) / days,
        "pump_ml": sum(float(p.amount or 0) for p in pumps),
        "pump_sessions": len(pumps),
        "night_share": night_feed_share(feeds),
        "last_feed": last_feed,
        "last_change": last_change,
        "latest_weight": latest_weight,
        "weight_gain": gain,
        "last_height": last_height,
        "last_head": last_head,
        "last_temp": last_temp,
        "methods": [{"name": k, "value": v} for k, v in method_counts.most_common()],
        "diaper_kinds": [
            {"name": k, "value": v} for k, v in diaper_kinds.most_common()
        ],
        "diaper_colors": [
            {"name": k, "value": v} for k, v in color_counts.most_common()
        ],
        "intervals": interval_histogram(intervals),
        "feed_hours": hourly_histogram([f.start for f in feeds]),
        "diaper_hours": hourly_histogram([c.time for c in changes]),
        "feed_daily": feed_daily,
        "feed_minutes_daily": feed_minutes_daily,
        "wet_daily": wet_daily,
        "solid_daily": solid_daily,
        "pump_daily": pump_daily,
        # Daily average of all weigh-ins that calendar day
        "weight_series": weight_daily_averages(weights),
        "height_series": [
            {
                "date": h.date.isoformat(),
                "label": h.date.strftime("%b %d"),
                "cm": _to_float(h.height),
            }
            for h in heights
        ],
        "head_series": [
            {
                "date": h.date.isoformat(),
                "label": h.date.strftime("%b %d"),
                "cm": _to_float(h.head_circumference),
            }
            for h in heads
        ],
        "temp_series": [
            {
                "time": timezone.localtime(t.time).isoformat(),
                "label": timezone.localtime(t.time).strftime("%b %d"),
                "c": _to_float(t.temperature),
            }
            for t in temps
        ],
        "recent": recent,
        "insights": build_insights(child, range_key),
        "lifetime_feeds": lifetime_feeds,
        "lifetime_changes": lifetime_changes,
        "synced_at": timezone.localtime(),
        "data_source": "Live Baby Buddy database",
        "hours_per_day": total_feed_min / 60.0 / days,
        "night_pct": int(round(night_feed_share(feeds) * 100)),
    }
