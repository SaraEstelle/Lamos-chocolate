"""
apps/cockpit/management/commands/seed_cockpit.py
================================================
Generate demo data for the executive cockpit: customers (with cantons) and
orders spread over the last ~90 days, across B2C and B2B channels.

Idempotent: demo customers use the '@demo.lamos' email domain, so every run
first wipes the previous demo dataset (and its orders) before reseeding.

    python manage.py seed_cockpit          # default 90 days
    python manage.py seed_cockpit --days 120
    python manage.py seed_cockpit --clear  # only remove demo data
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import B2BAccount, Customer
from apps.analytics.models import Event, EventTypeChoices
from apps.checkout.models import Order, OrderItem
from apps.common.constants import (
    B2BAccountStatusChoices,
    B2BSegmentChoices,
    ChannelChoices,
    CustomerTypeChoices,
)
from apps.customer_area.models import CustomerAddress
from apps.shop.models import SKU

DEMO_DOMAIN = "@demo.lamos"

# Canton distribution (weighted towards the French-speaking heartland).
CANTON_WEIGHTS = [
    ("VD", 28), ("GE", 22), ("ZH", 14), ("BE", 9), ("VS", 7),
    ("FR", 6), ("NE", 5), ("TI", 4), ("JU", 3), ("XX", 2),
]

# Representative locality + NPA (postal code) per canton, used to build a
# realistic default address. XX means "outside Switzerland".
CANTON_LOCALITIES = {
    "VD": ("Lausanne", "1003", "Suisse"),
    "GE": ("Genève", "1201", "Suisse"),
    "ZH": ("Zürich", "8001", "Suisse"),
    "BE": ("Berne", "3011", "Suisse"),
    "VS": ("Sion", "1950", "Suisse"),
    "FR": ("Fribourg", "1700", "Suisse"),
    "NE": ("Neuchâtel", "2000", "Suisse"),
    "TI": ("Lugano", "6900", "Suisse"),
    "JU": ("Delémont", "2800", "Suisse"),
    "XX": ("Annemasse", "74100", "France"),
}

# Order status mix (most orders are realised; a few pending/cancelled).
STATUS_WEIGHTS = [
    ("delivered", 40), ("shipped", 22), ("processing", 12),
    ("paid", 14), ("pending", 8), ("cancelled", 4),
]

# Statuses that reach a completed purchase (mirrors selectors.PAID_STATUSES).
REALISED_STATUSES = {"delivered", "shipped", "processing", "paid"}

# Hour-of-day distribution for orders/sessions: low overnight, lunch peak
# (12-13h) and a strong evening peak (19-21h). Index = hour (0-23).
HOUR_WEIGHTS = [
    1, 1, 1, 1, 1, 1, 2, 4, 7, 9, 11, 13,        # 00-11
    16, 15, 11, 10, 11, 13, 17, 22, 21, 15, 8, 4,  # 12-23
]
_HOURS = list(range(24))

CAMPAIGNS = ["", "", "", "Saint-Valentin", "Paques"]


def _weighted_choice(pairs):
    population, weights = zip(*pairs)
    return random.choices(population, weights=weights, k=1)[0]


def _stamp(day):
    """Return `day` with a realistic random time-of-day (peak hours weighted)."""
    hour = random.choices(_HOURS, weights=HOUR_WEIGHTS, k=1)[0]
    return day.replace(
        hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59),
    )


class Command(BaseCommand):
    help = "Seed demo customers and orders for the executive cockpit."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90,
                            help="Spread orders over the last N days.")
        parser.add_argument("--clear", action="store_true",
                            help="Only remove existing demo data, then exit.")

    @transaction.atomic
    def handle(self, *args, **options):
        self._clear_demo_data()
        if options["clear"]:
            self.stdout.write(self.style.SUCCESS("Demo data cleared."))
            return

        skus = list(SKU.objects.filter(is_active=True).select_related("product"))
        if not skus:
            self.stderr.write(
                "No active SKUs found. Load the shop fixtures first "
                "(loaddata products skus stock ...)."
            )
            return

        customers = self._create_customers()
        b2b_customers = [c for c in customers if c.customer_type != CustomerTypeChoices.B2C]

        order_count, item_count = self._create_orders(
            customers, b2b_customers, skus, options["days"]
        )
        event_count = Event.objects.filter(
            customer__email__endswith=DEMO_DOMAIN).count()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(customers)} customers, {order_count} orders, "
            f"{item_count} order items, {event_count} events "
            f"over {options['days']} days."
        ))

    # ------------------------------------------------------------------ #

    def _clear_demo_data(self):
        demo = Customer.objects.filter(email__endswith=DEMO_DOMAIN)
        # Orders RESTRICT on customer delete → remove orders (and items) first.
        OrderItem.objects.filter(order__customer__in=demo).delete()
        Order.objects.filter(customer__in=demo).delete()
        Event.objects.filter(customer__in=demo).delete()
        B2BAccount.objects.filter(customer__in=demo).delete()
        demo.delete()

    def _create_customers(self):
        customers = []

        # 40 B2C customers.
        for i in range(40):
            c = Customer.objects.create_user(
                email=f"client{i}{DEMO_DOMAIN}",
                password="demo-pass-123",
                first_name=f"Client{i}",
                last_name="Demo",
                customer_type=CustomerTypeChoices.B2C,
                consent_nlpd=True,
                consent_nlpd_at=timezone.now(),
            )
            self._create_default_address(c)
            customers.append(c)

        # 8 B2B customers (distributors + hospitality), each with a B2BAccount.
        b2b_specs = [
            (CustomerTypeChoices.B2B_DISTRIBUTOR, B2BSegmentChoices.DISTRIBUTOR),
            (CustomerTypeChoices.B2B_DISTRIBUTOR, B2BSegmentChoices.DISTRIBUTOR),
            (CustomerTypeChoices.B2B_DISTRIBUTOR, B2BSegmentChoices.DISTRIBUTOR),
            (CustomerTypeChoices.B2B_HOSPITALITY, B2BSegmentChoices.HOTEL),
            (CustomerTypeChoices.B2B_HOSPITALITY, B2BSegmentChoices.HOTEL),
            (CustomerTypeChoices.B2B_HOSPITALITY, B2BSegmentChoices.CORPORATE),
            (CustomerTypeChoices.B2B_HOSPITALITY, B2BSegmentChoices.CORPORATE),
            (CustomerTypeChoices.B2B_DISTRIBUTOR, B2BSegmentChoices.DISTRIBUTOR),
        ]
        for i, (ctype, segment) in enumerate(b2b_specs):
            company = f"Pro {segment.label} {i}"
            c = Customer.objects.create_user(
                email=f"pro{i}{DEMO_DOMAIN}",
                password="demo-pass-123",
                first_name=f"Pro{i}",
                last_name="Demo",
                company_name=company,
                is_b2b=True,
                customer_type=ctype,
                consent_nlpd=True,
                consent_nlpd_at=timezone.now(),
            )
            self._create_default_address(c, company=company)
            B2BAccount.objects.create(
                customer=c,
                company_name=company,
                client_number=f"B2B-{i:03d}",
                segment=segment,
                status=B2BAccountStatusChoices.ACTIVE,
                onboarded_at=timezone.now() - timedelta(days=random.randint(30, 200)),
            )
            customers.append(c)

        return customers

    def _create_default_address(self, customer, company=""):
        """Create the customer's default address; saving it denormalizes
        canton + npa onto the customer (see CustomerAddress.save)."""
        canton = _weighted_choice(CANTON_WEIGHTS)
        city, npa, country = CANTON_LOCALITIES[canton]
        CustomerAddress.objects.create(
            customer=customer,
            label="Demo",
            full_name=company or f"{customer.first_name} {customer.last_name}",
            line1=f"Rue du Commerce {random.randint(1, 99)}",
            city=city,
            postal_code=npa,
            canton=canton,
            country=country,
            is_default=True,
        )
        # Keep the in-memory instance in sync with the denormalized DB row,
        # so order creation can reuse customer.npa without a refetch.
        customer.canton = canton
        customer.npa = npa

    def _create_orders(self, customers, b2b_customers, skus, days):
        b2c_customers = [c for c in customers if c.customer_type == CustomerTypeChoices.B2C]
        products = list({s.product_id: s.product for s in skus}.values())
        now = timezone.now()
        order_count = 0
        item_count = 0
        events = []  # (Event, intended created_at) — backdated after bulk_create.

        for day_offset in range(days):
            day = now - timedelta(days=day_offset)
            # More recent days carry slightly more volume (linear ramp).
            recency = 1 - (day_offset / days)
            daily_orders = random.randint(1, 4 + int(recency * 5))

            for _ in range(daily_orders):
                is_b2b = random.random() < 0.25 and b2b_customers
                if is_b2b:
                    customer = random.choice(b2b_customers)
                    channel = ChannelChoices.B2B
                    line_count = random.randint(2, 5)
                    qty_range = (10, 80)  # bulk B2B quantities
                else:
                    customer = random.choice(b2c_customers)
                    channel = ChannelChoices.B2C
                    line_count = random.randint(1, 3)
                    qty_range = (1, 4)

                status = _weighted_choice(STATUS_WEIGHTS)
                order = Order.objects.create(
                    customer=customer,
                    order_number=Order.generate_order_number(),
                    status=status,
                    total_amount=0,
                    currency="CHF",
                    channel=channel,
                    campaign_period=random.choice(CAMPAIGNS),
                    shipping_country="CH",
                    shipping_postal_code=customer.npa,
                )

                total = 0
                chosen = random.sample(skus, min(line_count, len(skus)))
                for sku in chosen:
                    qty = random.randint(*qty_range)
                    item = OrderItem.objects.create(
                        order=order, sku=sku, quantity=qty, unit_price=sku.price,
                    )
                    total += item.subtotal
                    item_count += 1

                # Each order happens at a realistic time of day (peak hours).
                ts = _stamp(day)
                # auto_now_add ignores assignment on create → backdate via update().
                Order.objects.filter(pk=order.pk).update(
                    total_amount=total, created_at=ts, updated_at=ts,
                )
                order_count += 1

                # Converting funnel for this order: the customer browsed the
                # purchased products (plus a little extra), added to cart, began
                # checkout, and — for realised statuses — completed the purchase.
                viewed = {s.product for s in chosen}
                for p in random.sample(products, min(random.randint(0, 2), len(products))):
                    viewed.add(p)
                for p in viewed:
                    self._add_event(events, EventTypeChoices.PRODUCT_VIEW, customer,
                                    ts, channel, product=p)
                for s in chosen:
                    self._add_event(events, EventTypeChoices.ADD_TO_CART, customer,
                                    ts, channel, product=s.product)
                self._add_event(events, EventTypeChoices.BEGIN_CHECKOUT, customer,
                                ts, channel)
                if status in REALISED_STATUSES:
                    self._add_event(events, EventTypeChoices.PURCHASE, customer,
                                    ts, channel, value=total)

            # Abandoned sessions (no order): browsers that drop off, so the
            # funnel narrows realistically above the purchase line.
            for _ in range(random.randint(3, 8)):
                cust = random.choice(b2c_customers)
                ts = _stamp(day)
                browse = random.sample(products, random.randint(1, min(4, len(products))))
                for p in browse:
                    self._add_event(events, EventTypeChoices.PRODUCT_VIEW, cust,
                                    ts, ChannelChoices.B2C, product=p)
                if random.random() < 0.45:
                    self._add_event(events, EventTypeChoices.ADD_TO_CART, cust,
                                    ts, ChannelChoices.B2C, product=random.choice(browse))
                    if random.random() < 0.30:
                        self._add_event(events, EventTypeChoices.BEGIN_CHECKOUT, cust,
                                        ts, ChannelChoices.B2C)

            # Bounce sessions: a logged-in visit with no product view, so the
            # 'Utilisateurs' funnel stage sits above 'Visite page'.
            for _ in range(random.randint(2, 5)):
                cust = random.choice(b2c_customers)
                self._add_event(events, EventTypeChoices.LOGIN, cust,
                                _stamp(day), ChannelChoices.B2C)

        self._persist_events(events)
        return order_count, item_count

    def _add_event(self, events, event_type, customer, day, channel,
                   product=None, value=None):
        """Build an Event (unsaved) and remember its intended created_at."""
        e = Event(
            event_type=event_type,
            customer=customer,
            channel=channel or "",
            canton=customer.canton or "",
            value_chf=value,
            properties={"product_id": product.id} if product is not None else {},
        )
        events.append((e, day))

    def _persist_events(self, events):
        """Bulk-insert events, then backdate created_at (auto_now_add ignores it)."""
        if not events:
            return
        objs = [e for e, _ in events]
        Event.objects.bulk_create(objs, batch_size=500)
        for e, day in events:
            e.created_at = day
        Event.objects.bulk_update(objs, ["created_at"], batch_size=500)
