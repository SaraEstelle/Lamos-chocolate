"""
apps/cockpit/selectors.py
=========================
Read-only aggregations for the executive cockpit (PRD §8).

All KPIs are computed from the Order/OrderItem tables (the reliable source
filled by checkout), not from analytics events. Each function returns plain
dicts/lists so the view stays thin and the numbers are testable in isolation.
"""

from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import (
    Coalesce, ExtractHour, ExtractIsoWeekDay, TruncDate,
)
from django.utils import timezone

from apps.analytics.models import Event, EventTypeChoices
from apps.checkout.models import Order, OrderItem
from apps.cockpit.models import CantonTarget, CockpitObjective, ProductTarget
from apps.common.constants import SwissCantonChoices
from apps.shop.models import Product, Stock

# Margin amount per order line: (unit_price - production cost) * quantity.
# Coalesce guards SKUs without a recorded cost (treated as zero cost).
MARGIN_EXPR = ExpressionWrapper(
    (F("unit_price") - Coalesce(F("sku__cost_chf"), 0)) * F("quantity"),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)

# Statuses that count as realised (paid) revenue.
PAID_STATUSES = ("paid", "processing", "shipped", "delivered")
# Statuses that count as actually shipped units.
SHIPPED_STATUSES = ("shipped", "delivered")

def _pct(actual, target):
    """Return actual/target as a rounded percentage, guarding a zero target."""
    return round((float(actual) / target) * 100, 1) if target else 0.0


def get_pulse():
    """Headline 'Pulse' band: today + month-to-date vs targets.

    Targets are the Direction objectives set from the Pilotage tab.
    """
    today = timezone.localdate()
    month_start = today.replace(day=1)
    obj = CockpitObjective.load()

    paid = Order.objects.filter(status__in=PAID_STATUSES)

    revenue_today = paid.filter(created_at__date=today).aggregate(
        t=Sum("total_amount"))["t"] or 0
    revenue_mtd = paid.filter(created_at__date__gte=month_start).aggregate(
        t=Sum("total_amount"))["t"] or 0
    orders_today = Order.objects.filter(created_at__date=today).count()
    units_mtd = OrderItem.objects.filter(
        order__status__in=SHIPPED_STATUSES,
        order__created_at__date__gte=month_start,
    ).aggregate(q=Sum("quantity"))["q"] or 0

    return {
        "revenue_today": revenue_today,
        "revenue_today_target": obj.daily_revenue_chf,
        "revenue_today_pct": _pct(revenue_today, obj.daily_revenue_chf),
        "revenue_mtd": revenue_mtd,
        "revenue_mtd_target": obj.monthly_revenue_chf,
        "revenue_mtd_pct": _pct(revenue_mtd, obj.monthly_revenue_chf),
        "orders_today": orders_today,
        "units_mtd": units_mtd,
        "capacity_units": obj.monthly_capacity_units,
        "units_mtd_pct": _pct(units_mtd, obj.monthly_capacity_units),
    }


def get_channel_split(days=30):
    """Revenue + order count split by channel (B2C vs B2B) for the donut."""
    since = timezone.now() - timedelta(days=days)
    return list(
        Order.objects
        .filter(status__in=PAID_STATUSES, created_at__gte=since)
        .values("channel")
        .annotate(revenue=Sum("total_amount"), orders=Count("id"))
        .order_by("-revenue")
    )


def get_top_skus(days=30, limit=8):
    """Best-selling SKUs by units sold over the period."""
    since = timezone.now() - timedelta(days=days)
    return list(
        OrderItem.objects
        .filter(order__status__in=PAID_STATUSES, order__created_at__gte=since)
        .values("sku__sku_code", "sku__product__name_fr", "sku__flavor")
        .annotate(units=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-units")[:limit]
    )


def get_revenue_trend(days=30):
    """Daily realised revenue over the period (for the trend line)."""
    since = timezone.now() - timedelta(days=days)
    return list(
        Order.objects
        .filter(status__in=PAID_STATUSES, created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("total_amount"))
        .order_by("day")
    )


def get_canton_revenue(days=90):
    """Realised revenue + order count per Swiss canton (sales heatmap).

    Canton comes from the customer (denormalized from their default address).
    Each row carries a `share` (% of total) and an `intensity` (0..1 relative
    to the strongest canton) so the template can shade the heat cells.
    """
    since = timezone.now() - timedelta(days=days)
    rows = list(
        Order.objects
        .filter(status__in=PAID_STATUSES, created_at__gte=since)
        .values("customer__canton")
        .annotate(revenue=Sum("total_amount"), orders=Count("id"))
        .order_by("-revenue")
    )

    labels = dict(SwissCantonChoices.choices)
    total = sum(float(r["revenue"] or 0) for r in rows)
    max_rev = max((float(r["revenue"] or 0) for r in rows), default=0)

    result = []
    for r in rows:
        code = r["customer__canton"] or ""
        revenue = float(r["revenue"] or 0)
        result.append({
            "code": code or "—",
            "label": labels.get(code, "Non renseigné"),
            "revenue": revenue,
            "orders": r["orders"],
            "share": round(revenue / total * 100, 1) if total else 0.0,
            "intensity": round(revenue / max_rev, 3) if max_rev else 0.0,
        })

    return {
        "rows": result,
        "total": total,
        "days": days,
        "canton_count": len(result),
    }


def get_product_overview(days=90):
    """Per-product study: units, revenue, share, gross margin, stock.

    Margin here is GROSS (revenue - production cost), it excludes transport
    which is not modelled per product line. See get_product_detail for the
    SKU/flavor breakdown.
    """
    since = timezone.now() - timedelta(days=days)
    items = OrderItem.objects.filter(
        order__status__in=PAID_STATUSES, order__created_at__gte=since,
    )
    rows = list(
        items
        .values(
            "sku__product_id",
            "sku__product__name_fr",
            "sku__product__category__name_fr",
        )
        .annotate(
            units=Sum("quantity"),
            revenue=Sum("subtotal"),
            orders=Count("order", distinct=True),
            margin_amount=Sum(MARGIN_EXPR),
        )
        .order_by("-revenue")
    )

    # Total stock on hand per product (across its SKUs).
    stock_map = {
        p["id"]: p["stock"] or 0
        for p in Product.objects.values("id").annotate(
            stock=Sum("skus__stock__quantity"))
    }

    total = sum(float(r["revenue"] or 0) for r in rows)
    total_margin = sum(float(r["margin_amount"] or 0) for r in rows)

    result = []
    for r in rows:
        revenue = float(r["revenue"] or 0)
        margin = float(r["margin_amount"] or 0)
        pid = r["sku__product_id"]
        result.append({
            "id": pid,
            "name": r["sku__product__name_fr"],
            "category": r["sku__product__category__name_fr"],
            "units": r["units"],
            "revenue": revenue,
            "orders": r["orders"],
            "share": round(revenue / total * 100, 1) if total else 0.0,
            "margin_pct": round(margin / revenue * 100, 1) if revenue else 0.0,
            "stock": stock_map.get(pid, 0),
        })

    return {
        "rows": result,
        "total": total,
        "days": days,
        "product_count": len(result),
        "avg_margin_pct": round(total_margin / total * 100, 1) if total else 0.0,
    }


def get_product_detail(product_id, days=90):
    """Drill-down for one product: KPIs, channel split, SKU/flavor breakdown,
    daily revenue trend. Returns None if the product does not exist."""
    product = Product.objects.select_related("category").filter(pk=product_id).first()
    if product is None:
        return None

    since = timezone.now() - timedelta(days=days)
    items = OrderItem.objects.filter(
        sku__product_id=product_id,
        order__status__in=PAID_STATUSES,
        order__created_at__gte=since,
    )

    agg = items.aggregate(
        units=Sum("quantity"),
        revenue=Sum("subtotal"),
        orders=Count("order", distinct=True),
        margin_amount=Sum(MARGIN_EXPR),
    )
    revenue = float(agg["revenue"] or 0)
    margin = float(agg["margin_amount"] or 0)
    kpis = {
        "units": agg["units"] or 0,
        "revenue": revenue,
        "orders": agg["orders"] or 0,
        "margin_pct": round(margin / revenue * 100, 1) if revenue else 0.0,
    }

    channel = [
        {"channel": c["order__channel"], "revenue": float(c["revenue"] or 0)}
        for c in items.values("order__channel")
        .annotate(revenue=Sum("subtotal"))
        .order_by("-revenue")
    ]

    # Current stock per SKU, to flag low stock in the breakdown.
    stock_map = {
        s["sku__sku_code"]: s
        for s in Stock.objects.filter(sku__product_id=product_id)
        .values("sku__sku_code", "quantity", "threshold_alert")
    }

    sku_rows = []
    for s in (
        items.values("sku__sku_code", "sku__format", "sku__flavor")
        .annotate(units=Sum("quantity"), revenue=Sum("subtotal"),
                  margin_amount=Sum(MARGIN_EXPR))
        .order_by("-revenue")
    ):
        rev = float(s["revenue"] or 0)
        m = float(s["margin_amount"] or 0)
        st = stock_map.get(s["sku__sku_code"], {})
        qty = st.get("quantity")
        thr = st.get("threshold_alert")
        sku_rows.append({
            "code": s["sku__sku_code"],
            "format": s["sku__format"],
            "flavor": s["sku__flavor"],
            "units": s["units"],
            "revenue": rev,
            "margin_pct": round(m / rev * 100, 1) if rev else 0.0,
            "stock": qty if qty is not None else 0,
            "is_low": qty is not None and thr is not None and qty <= thr,
        })

    trend = list(
        items.annotate(day=TruncDate("order__created_at"))
        .values("day")
        .annotate(total=Sum("subtotal"))
        .order_by("day")
    )

    return {
        "product": {
            "id": product.id,
            "name": product.name_fr,
            "category": product.category.name_fr,
        },
        "kpis": kpis,
        "channel": channel,
        "sku_rows": sku_rows,
        "trend": trend,
        "days": days,
    }


def get_inventory_forecast(window_days=30):
    """Inventory runway + production relaunch alerts (PRD/US-22 KPIs 5 & 6).

    KPI 5 — days until stockout per SKU: current stock / sales velocity, where
    velocity is units sold over the window divided by the window length.
    KPI 6 — production relaunch alerts: SKUs that will run out before a new
    batch can be produced (runway <= production lead time), or already low.

    Reuses the forecasting model's fields (`Stock.is_low`,
    `SKU.production_delay_days`, `SKU.batch_size`).
    """
    since = timezone.now() - timedelta(days=window_days)
    sold = {
        r["sku_id"]: r["units"]
        for r in OrderItem.objects.filter(
            order__status__in=PAID_STATUSES, order__created_at__gte=since,
        ).values("sku_id").annotate(units=Sum("quantity"))
    }

    rows = []
    critical_count = warning_count = 0
    for stock in Stock.objects.select_related("sku__product"):
        sku = stock.sku
        if not sku.is_active:
            continue

        units = sold.get(sku.id, 0)
        velocity = units / window_days if window_days else 0  # units/day
        days_left = round(stock.quantity / velocity, 1) if velocity > 0 else None
        lead = sku.production_delay_days

        if days_left is not None and days_left <= lead:
            status = "critical"
            critical_count += 1
        elif stock.is_low or (days_left is not None and days_left <= lead * 2):
            status = "warning"
            warning_count += 1
        else:
            status = "ok"

        rows.append({
            "code": sku.sku_code,
            "product": sku.product.name_fr,
            "flavor": sku.flavor,
            "stock": stock.quantity,
            "threshold": stock.threshold_alert,
            "velocity": round(velocity, 2),
            "days_left": days_left,
            "lead_days": lead,
            "batch_size": sku.batch_size,
            "is_low": stock.is_low,
            "status": status,
            "needs_restock": status in ("critical", "warning"),
        })

    # Shortest runway first; SKUs with no sales (days_left None) go last.
    rows.sort(key=lambda r: (r["days_left"] is None,
                             r["days_left"] if r["days_left"] is not None else 0))
    alerts = [r for r in rows if r["needs_restock"]]

    return {
        "rows": rows,
        "alerts": alerts,
        "window_days": window_days,
        "sku_count": len(rows),
        "critical_count": critical_count,
        "warning_count": warning_count,
    }


def get_pilotage(days=30):
    """Pilotage tab: Direction objectives + actual-vs-target per product.

    Returns the editable objectives row plus, for each active product, the
    units sold and gross margin % over the window, the monthly unit objective,
    and the resulting fill rate. Drives both the form (current values) and the
    comparison table.
    """
    obj = CockpitObjective.load()
    since = timezone.now() - timedelta(days=days)

    sold = {
        r["sku__product_id"]: r
        for r in OrderItem.objects.filter(
            order__status__in=PAID_STATUSES, order__created_at__gte=since,
        )
        .values("sku__product_id")
        .annotate(
            units=Sum("quantity"),
            revenue=Sum("subtotal"),
            margin_amount=Sum(MARGIN_EXPR),
        )
    }
    targets = {
        t.product_id: t.monthly_units for t in ProductTarget.objects.all()
    }

    products = []
    total_target = total_actual = 0
    for p in Product.objects.filter(is_active=True).order_by("name_fr"):
        agg = sold.get(p.id, {})
        units = agg.get("units", 0) or 0
        revenue = float(agg.get("revenue", 0) or 0)
        margin = float(agg.get("margin_amount", 0) or 0)
        target = targets.get(p.id, 0)
        margin_pct = round(margin / revenue * 100, 1) if revenue else 0.0
        products.append({
            "id": p.id,
            "name": p.name_fr,
            "actual_units": units,
            "target_units": target,
            "fill_pct": round(units / target * 100, 1) if target else None,
            "margin_pct": margin_pct,
            "margin_gap": round(margin_pct - float(obj.target_margin_pct), 1),
        })
        # Totals cover only products with an objective (like-for-like fill).
        if target:
            total_target += target
            total_actual += units

    # Per-canton revenue objective vs realised revenue over the window.
    canton_rev = {
        r["customer__canton"]: float(r["revenue"] or 0)
        for r in Order.objects.filter(
            status__in=PAID_STATUSES, created_at__gte=since,
        ).values("customer__canton").annotate(revenue=Sum("total_amount"))
    }
    canton_targets = {
        t.canton: t.monthly_revenue_chf for t in CantonTarget.objects.all()
    }
    cantons = []
    total_canton_target = total_canton_actual = 0
    for code, label in SwissCantonChoices.choices:
        actual = canton_rev.get(code, 0)
        target = canton_targets.get(code, 0)
        cantons.append({
            "code": code,
            "label": label,
            "actual_revenue": actual,
            "target_revenue": target,
            "fill_pct": round(actual / target * 100, 1) if target else None,
        })
        # Totals cover only cantons with an objective, so the fill rate compares
        # like-for-like (realised vs target on the same perimeter).
        if target:
            total_canton_target += target
            total_canton_actual += actual
    # Strongest realised revenue first; the long tail of empty cantons sinks down.
    cantons.sort(key=lambda c: (-c["actual_revenue"], c["label"]))

    return {
        "objective": obj,
        "products": products,
        "cantons": cantons,
        "days": days,
        "total_target_units": total_target,
        "total_actual_units": total_actual,
        "total_fill_pct": (
            round(total_actual / total_target * 100, 1) if total_target else None
        ),
        "total_canton_target": total_canton_target,
        "total_canton_actual": total_canton_actual,
        "total_canton_fill_pct": (
            round(total_canton_actual / total_canton_target * 100, 1)
            if total_canton_target else None
        ),
    }


# French short weekday labels, ISO order (1 = Monday … 7 = Sunday).
_WEEKDAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def get_orders_by_weekday(days=90):
    """Order count per day of week over the period (Mon → Sun bar plot)."""
    since = timezone.now() - timedelta(days=days)
    counts = {
        r["wd"]: r["n"]
        for r in Order.objects.filter(created_at__gte=since)
        .annotate(wd=ExtractIsoWeekDay("created_at"))
        .values("wd")
        .annotate(n=Count("id"))
    }
    bars = [
        {"label": _WEEKDAY_LABELS[i], "count": counts.get(i + 1, 0)}
        for i in range(7)
    ]
    return {"days": days, "bars": bars, "total": sum(b["count"] for b in bars)}


def get_orders_by_hour(days=90):
    """Order count per hour of day (0-23) to surface peak ordering hours."""
    since = timezone.now() - timedelta(days=days)
    counts = {
        r["h"]: r["n"]
        for r in Order.objects.filter(created_at__gte=since)
        .annotate(h=ExtractHour("created_at"))
        .values("h")
        .annotate(n=Count("id"))
    }
    bars = [{"label": f"{h:02d}h", "count": counts.get(h, 0)} for h in range(24)]
    peak = max(bars, key=lambda b: b["count"]) if any(b["count"] for b in bars) else None
    return {
        "days": days,
        "bars": bars,
        "peak_hour": peak["label"] if peak else None,
        "peak_count": peak["count"] if peak else 0,
    }


def get_funnel(days=90):
    """Conversion funnel by session (a session = one customer on one day).

    Counting distinct customers over a long window is degenerate here (almost
    everyone eventually does everything), so the unit is the *session*: how
    many visits reached each step. Stages: active users → product view → add to
    cart → begin checkout → purchase. Each stage shows its share of the top and
    the step-to-step conversion rate.
    """
    since = timezone.now() - timedelta(days=days)
    events = Event.objects.filter(created_at__gte=since)

    def sessions(event_type=None):
        qs = events if event_type is None else events.filter(event_type=event_type)
        return (
            qs.annotate(d=TruncDate("created_at"))
            .values("customer", "d").distinct().count()
        )

    raw = [
        ("Utilisateurs", sessions()),
        ("Visite page", sessions(EventTypeChoices.PRODUCT_VIEW)),
        ("Ajout panier", sessions(EventTypeChoices.ADD_TO_CART)),
        ("Checkout", sessions(EventTypeChoices.BEGIN_CHECKOUT)),
        ("Validé", sessions(EventTypeChoices.PURCHASE)),
    ]

    top = raw[0][1] or 0
    stages = []
    for i, (label, count) in enumerate(raw):
        prev = raw[i - 1][1] if i > 0 else count
        stages.append({
            "label": label,
            "count": count,
            "pct_of_top": round(count / top * 100, 1) if top else 0.0,
            "pct_from_prev": round(count / prev * 100, 1) if prev else None,
        })

    return {
        "days": days,
        "stages": stages,
        "overall_conversion": (
            round(raw[-1][1] / top * 100, 1) if top else 0.0
        ),
    }


def get_top_viewed(days=90, limit=5):
    """Most-viewed products from product_view events (properties.product_id)."""
    since = timezone.now() - timedelta(days=days)
    rows = list(
        Event.objects
        .filter(event_type=EventTypeChoices.PRODUCT_VIEW, created_at__gte=since)
        .values("properties__product_id")
        .annotate(views=Count("id"))
        .order_by("-views")[:limit]
    )
    ids = [r["properties__product_id"] for r in rows if r["properties__product_id"]]
    names = {
        p["id"]: p["name_fr"]
        for p in Product.objects.filter(id__in=ids).values("id", "name_fr")
    }
    return [
        {
            "id": r["properties__product_id"],
            "name": names.get(r["properties__product_id"], "—"),
            "views": r["views"],
        }
        for r in rows
    ]


def get_top_ordered(days=90, limit=5):
    """Best-selling products by units ordered over the period."""
    since = timezone.now() - timedelta(days=days)
    return list(
        OrderItem.objects
        .filter(order__status__in=PAID_STATUSES, order__created_at__gte=since)
        .values("sku__product_id", "sku__product__name_fr")
        .annotate(units=Sum("quantity"), revenue=Sum("subtotal"))
        .order_by("-units")[:limit]
    )
