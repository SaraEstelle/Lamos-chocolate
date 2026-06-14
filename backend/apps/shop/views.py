"""
apps/shop/views.py
==================
Public catalog views (no authentication required).

Four class-based views:
1. CatalogView       — list active products (paginated, optional ?category=)
2. CategoryView      — products of a single category (by slug)
3. SearchView        — search products by name/description (?q=)
4. ProductDetailView — product detail with SKUs, images and delivery estimates
"""

from django.views.generic import DetailView, ListView

from apps.shop import filters, selectors, services
from apps.shop.forms import SearchForm

PRODUCTS_PER_PAGE = 12


class CatalogView(ListView):
    """List of active products, with optional ``?category=<slug>`` filtering."""

    template_name = "shop/catalog.html"
    context_object_name = "products"
    paginate_by = PRODUCTS_PER_PAGE

    def get_queryset(self):
        products = selectors.get_active_products()
        category_slug = self.request.GET.get("category")
        return filters.filter_by_category(products, category_slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = selectors.get_all_categories()
        context["active_category"] = self.request.GET.get("category", "")
        return context


class CategoryView(CatalogView):
    """Products of a single category, addressed by slug in the URL."""

    def get_queryset(self):
        self.category = selectors.get_category_by_slug(self.kwargs["slug"])
        return filters.filter_by_category(
            selectors.get_active_products(), self.category.slug
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["active_category"] = self.category.slug
        return context


class SearchView(CatalogView):
    """Search products by name/description via the ``?q=`` parameter."""

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        self.query = ""
        if self.form.is_valid():
            self.query = self.form.cleaned_data["q"]
        return filters.search_products(selectors.get_active_products(), self.query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["search_query"] = self.query
        return context


class ProductDetailView(DetailView):
    """Detail of an active product: SKUs, images and per-zone delivery times."""

    template_name = "shop/product.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return selectors.get_product_by_slug(self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        # Active SKUs are filtered in Python to reuse the prefetched relation.
        skus = [sku for sku in product.skus.all() if sku.is_active]
        for sku in skus:
            sku.delivery_estimates = services.get_delivery_estimates(sku)
        context["skus"] = skus
        context["images"] = product.images.all()
        return context
