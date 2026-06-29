/* ============================================================================
   LAMOS — main.js
   Replaces Bootstrap's bundle for the features we actually use:
   - mobile burger menu toggle (accessible: aria-expanded)
   - reveal-on-scroll via IntersectionObserver
   ============================================================================ */
(function () {
  "use strict";

  // 1. Mobile navigation toggle
  var burger = document.querySelector(".nav-burger");
  var links = document.getElementById("primary-nav");
  if (burger && links) {
    burger.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close the menu when a link is clicked (mobile UX)
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        links.classList.remove("is-open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }

  // 1b. Add-to-cart without leaving the page (progressive enhancement).
  //     Falls back to a normal form POST if anything goes wrong.
  function showToast(message, isError) {
    var host = document.getElementById("toast-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "toast-host";
      host.className = "toast-host";
      document.body.appendChild(host);
    }
    var toast = document.createElement("div");
    toast.className = "toast" + (isError ? " toast--error" : "");
    toast.setAttribute("role", "status");
    toast.textContent = message;
    host.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add("is-visible"); });
    setTimeout(function () {
      toast.classList.remove("is-visible");
      setTimeout(function () { toast.remove(); }, 300);
    }, 2600);
  }

  function updateCartBadge(count) {
    var badge = document.querySelector("[data-cart-count]");
    if (!badge) return;
    badge.textContent = count;
    if (count > 0) {
      badge.removeAttribute("hidden");
    } else {
      badge.setAttribute("hidden", "");
    }
  }

  document.querySelectorAll("form[data-cart-add]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = form.querySelector("[type=submit]");
      if (btn) btn.disabled = true;
      fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
        credentials: "same-origin",
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          if (res.ok) {
            updateCartBadge(res.data.total_items);
            showToast(form.dataset.addedLabel || "Added to your cart.", false);
          } else {
            showToast(res.data.error || "Could not add to cart.", true);
          }
        })
        .catch(function () { form.submit(); })  // network error → full POST fallback
        .finally(function () { if (btn) btn.disabled = false; });
    });
  });

  // 1c. Cart page: update / remove without reloading.
  function bindCartMutation(selector, labelKey) {
    document.querySelectorAll(selector).forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var btn = form.querySelector("[type=submit]");
        if (btn) btn.disabled = true;
        var skuField = form.querySelector("[name=sku_id]");
        var skuId = skuField ? skuField.value : null;
        fetch(form.action, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: new FormData(form),
          credentials: "same-origin",
        })
          .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
          .then(function (res) {
            if (!res.ok) { showToast(res.data.error || "Could not update cart.", true); return; }
            var data = res.data;
            updateCartBadge(data.total_items);
            if (data.is_empty) { window.location.reload(); return; }

            var item = data.items.filter(function (it) { return String(it.sku_id) === String(skuId); })[0];
            var row = document.querySelector('tr[data-sku-id="' + skuId + '"]');
            if (item) {
              if (row) {
                var st = row.querySelector("[data-subtotal]");
                if (st) st.textContent = item.subtotal + " " + item.currency;
                var qn = row.querySelector("[name=quantity]");
                if (qn) qn.value = item.quantity;
              }
            } else if (row) {
              row.remove();  // quantity set to 0 or removed
            }

            var totalEl = document.querySelector("[data-cart-total]");
            if (totalEl) totalEl.textContent = data.total_price;
            var countEl = document.querySelector("[data-cart-count-text]");
            if (countEl) countEl.textContent = data.total_items;
            showToast(form.dataset[labelKey] || "Cart updated.", false);
          })
          .catch(function () { form.submit(); })
          .finally(function () { if (btn) btn.disabled = false; });
      });
    });
  }
  bindCartMutation("form[data-cart-update]", "updatedLabel");
  bindCartMutation("form[data-cart-remove]", "removedLabel");

  // 2. Reveal-on-scroll
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }
})();