/* ============================================================================
   LAMOS — main.js  (à placer dans backend/static/js/main.js)
   Remplace le bundle Bootstrap. Vanilla JS, aucune dépendance.
   - menu burger responsive (accessible)
   - reveal-on-scroll (IntersectionObserver)
   - filtre boutique par catégorie (client-side)
   - bannière de consentement cookies
   ============================================================================ */
(function () {
  "use strict";

  /* 1. Menu burger ---------------------------------------------------------- */
  var burger = document.querySelector(".nav-burger");
  var links = document.getElementById("primary-nav");
  if (burger && links) {
    burger.addEventListener("click", function () {
      var open = links.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        links.classList.remove("is-open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* 2. Reveal-on-scroll ----------------------------------------------------- */
  var reveals = document.querySelectorAll(".reveal, .reveal-left, .reveal-right");
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

  /* 3. Filtre boutique ------------------------------------------------------ */
  var filterBar = document.getElementById("shop-filters");
  var grid = document.getElementById("product-grid");
  if (filterBar && grid) {
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest(".filter-btn");
      if (!btn) return;
      filterBar.querySelectorAll(".filter-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      var f = btn.getAttribute("data-filter");
      grid.querySelectorAll(".product-card").forEach(function (card) {
        var show = (f === "all") || (card.getAttribute("data-category") === f);
        card.style.display = show ? "" : "none";
      });
    });
  }

  /* 4. Bannière cookies ----------------------------------------------------- */
  var banner = document.getElementById("cookie-banner");
  if (!banner) return;
  function getCookie(name) {
    return document.cookie.split("; ").reduce(function (r, c) {
      var p = c.split("="); return p[0] === name ? decodeURIComponent(p[1]) : r;
    }, "");
  }
  if (document.cookie.indexOf("lamos_consent=") === -1) banner.hidden = false;

  function send(analytics, marketing) {
    return fetch("/consent/set/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ analytics: analytics, marketing: marketing })
    }).then(function () { banner.hidden = true; });
  }
  banner.addEventListener("click", function (e) {
    var action = e.target.getAttribute("data-consent");
    var prefs = banner.querySelector(".cookie-banner__prefs");
    if (action === "accept") send(true, true);
    else if (action === "reject") send(false, false);
    else if (action === "customize" && prefs) prefs.hidden = !prefs.hidden;
    else if (action === "save") {
      var a = document.getElementById("consent-analytics");
      var m = document.getElementById("consent-marketing");
      send(a && a.checked, m && m.checked);
    }
  });
  var manage = document.getElementById("manage-cookies");
  if (manage) manage.addEventListener("click", function (e) { e.preventDefault(); banner.hidden = false; });
})();
