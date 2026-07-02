/* =============================================================================
   auth-slide.js  —  bascule de la carte glissante + afficher/masquer le mdp
   -----------------------------------------------------------------------------
   >>> PLACER CE FICHIER DANS :  backend/static/js/auth-slide.js
   -----------------------------------------------------------------------------
   JavaScript "vanilla" (aucune dépendance). Chargé par les pages d'accès
   (accounts/access.html et b2b/access.html) via {% block extra_scripts %}.

   Rôle :
   1) Faire glisser la carte entre "connexion" et "inscription" (B2C uniquement ;
      le B2B n'a pas de bascule, son panneau doré est un simple lien).
   2) Afficher / masquer le mot de passe au clic sur l'œil.
   ========================================================================== */
(function () {
  "use strict";

  // La carte glissante. Sur le B2B (login seul) elle existe aussi, mais il n'y
  // a pas de boutons [data-auth] -> la bascule ne fait simplement rien.
  var card = document.getElementById("authCard");

  // --- 1) Bascule connexion <-> inscription (B2C) ---------------------------
  if (card) {
    // Tout élément [data-auth="register"] ouvre le côté inscription...
    document.querySelectorAll('[data-auth="register"]').forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        card.classList.add("mode-register");
      });
    });
    // ...et [data-auth="signin"] revient au côté connexion.
    document.querySelectorAll('[data-auth="signin"]').forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        card.classList.remove("mode-register");
      });
    });
  }

  // --- 2) Afficher / masquer le mot de passe --------------------------------
  // Fonctionne pour CHAQUE bouton .password-toggle : il bascule le type de
  // l'<input> voisin entre "password" et "text". (Aucun mot de passe n'est
  // envoyé nulle part : c'est purement visuel, côté navigateur.)
  document.querySelectorAll(".password-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = btn.parentElement.querySelector("input");
      if (!input) { return; }
      var hidden = input.type === "password";
      input.type = hidden ? "text" : "password";
      btn.textContent = hidden ? "🙈" : "👁";
    });
  });
})();

