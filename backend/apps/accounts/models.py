"""
apps/accounts/models.py
=======================
Modèles d'authentification et gestion des comptes clients.

Modèles :
1. Customer — Utilisateur du système (remplace Django User)
2. PasswordResetToken — Token pour réinitialisation de mot de passe

Règulation Suisse (RGPD) :
- Stockage du mot de passe sécurisé (hashe)
- Email unique et vérifié
- Droit d'accès aux données personnelles
- Droit à l'oubli (suppression du compte)
"""

import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _
from apps.common.constants import CustomerTypeChoices, SwissCantonChoices
from apps.common.constants import B2BSegmentChoices, B2BAccountStatusChoices

class CustomerManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle Customer.

    Django permet de personaliser la création de User.
    Ici on crée des clients avec email au lieu de username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Créer un client normal.
        """
        if not email:
            raise ValueError(_('Email is required'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Créer un superuser (admin).
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Customer(AbstractBaseUser, PermissionsMixin):
    """
    Modèle Client personnalisé (remplace Django User).

    Champs :
    - id : UUID unique (plus sécurisé que les entiers)
    - email : Email unique (identifiant)
    - first_name, last_name : Nom et prénom
    - phone : Téléphone pour les commandes
    - company_name : Nom de l'entreprise (si B2B)
    - is_b2b : Flag pour distinguer clients B2C et B2B
    - is_active : Compte activé ou désactivé
    - is_staff : Accès à /admin/ (superuser)
    - created_at, updated_at : Dates de création et modification

    Sécurité :
    - UUID : impossible de deviner l'ID d'un autre client
    - Password : hashe automatiquement par Django
    - Email unique : empêche les doublons
    """

    # Identifiant unique (UUID au lieu d'integer)
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identifiant unique du client (UUID)"
    )

    # Email (utilisé pour login au lieu de username)
    email = models.EmailField(
        unique=True,
        help_text="Email unique du client"
    )

    # Informations personnelles
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Prénom du client"
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nom de famille du client"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numéro de téléphone (format: +41 XX XXX XX XX)"
    )

    # B2B
    company_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nom de l'entreprise (si client B2B)"
    )

    is_b2b = models.BooleanField(
        default=False,
        help_text="Vrai si c'est un client B2B (professionnel)"
    )

    # Langue préférée
    preferred_language = models.CharField(
        max_length=10,
        default='fr',
        choices=[
            ('fr', 'Français'),
            ('en', 'English'),
            ('de-ch', 'Deutsch (Schweiz)'),
            ('it-ch', 'Italiano (Svizzera)'),
        ],
        help_text="Langue préférée du client"
    )

    # --- Strategic fields for KPIs and the executive cockpit ---
    customer_type = models.CharField(
        max_length=20,
        choices=CustomerTypeChoices.choices,
        default=CustomerTypeChoices.B2C,
        help_text="Segment used across KPIs (B2C / B2B distributor / B2B hospitality)",
    )
    npa = models.CharField(
        max_length=10, blank=True, default="",
        help_text="Swiss postal code (NPA)",
    )
    canton = models.CharField(
        max_length=2, blank=True, default="",
        choices=SwissCantonChoices.choices,
        help_text="Swiss canton (for the sales heatmap)",
    )
    source_acquisition = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Acquisition source (utm_source or similar)",
    )
    consent_nlpd = models.BooleanField(
        default=False,
        help_text="Swiss nLPD data-processing consent",
    )
    consent_nlpd_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When nLPD consent was given",
    )

    # Statut
    is_active = models.BooleanField(
        default=True,
        help_text="Le compte est-il actif ? (False = compte suspendu)"
    )

    is_staff = models.BooleanField(
        default=False,
        help_text="Accès à l'interface admin (/admin/)"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du compte"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date de dernière modification"
    )

    # Gestionnaire personnalisé
    objects = CustomerManager()

    # Champs utilisés pour l'authentification et l'admin
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ['-created_at']

    def __str__(self):
        """Affichage du client dans l'admin"""
        return f"{self.email} ({self.first_name} {self.last_name})"

    def get_full_name(self):
        """Retourner le nom complet"""
        return f"{self.first_name} {self.last_name}".strip()


class PasswordResetToken(models.Model):
    """
    Token pour réinitialisation de mot de passe.

    Quand un client demande "oublié mot de passe" :
    1. On crée un PasswordResetToken unique
    2. On envoie par email : https://lamos.ch/accounts/reset/TOKEN
    3. Le client clique sur le lien
    4. Il peut changer son mot de passe
    5. Le token est supprimé (sécurité)

    Sécurité :
    - Token : chaîne aléatoire longue (impossible de deviner)
    - Expiration : 1h (après c'est invalid)
    - Une seule utilisation (suppression après)
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Client concerné
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text="Client qui demande la réinitialisation"
    )

    # Token unique (chaîne aléatoire)
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token aléatoire envoyé par email"
    )

    # Expiration (1h)
    expires_at = models.DateTimeField(
        help_text="Date d.expiration du token (1h)"
    )

    # Création
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du token"
    )

    # Flag d'utilisation
    is_used = models.BooleanField(
        default=False,
        help_text="True si le token a déjà été utilisé"
    )

    class Meta:
        verbose_name = _("Password Reset Token")
        verbose_name_plural = _("Password Reset Tokens")
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.customer.email}"

    def is_valid(self):
        """
        Vérifier si le token est encore valide.

        Valide si :
        - Pas expiré
        - Pas encore utilisé
        """
        from django.utils import timezone

        # Vérifier l'expiration
        if timezone.now() > self.expires_at:
            return False

        # Vérifier qu'il n'a pas été utilisé
        if self.is_used:
            return False

        return True

class B2BAccount(models.Model):
    """
    Professional account details, one-to-one with a B2B Customer.

    Holds the commercial information used by the B2B portal and the cockpit
    pipeline (segment, price list, lifecycle status).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="b2b_account",   # access via customer.b2b_account
    )
    company_name = models.CharField(max_length=200)
    client_number = models.CharField(max_length=50, blank=True, default="")
    segment = models.CharField(
        max_length=20,
        choices=B2BSegmentChoices.choices,
        default=B2BSegmentChoices.DISTRIBUTOR,
    )
    payment_terms = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=B2BAccountStatusChoices.choices,
        default=B2BAccountStatusChoices.PROSPECT,
    )
    onboarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "b2b_accounts"

    def __str__(self):
        return f"{self.company_name} ({self.get_segment_display()})"

class ConsentLog(models.Model):
    """
    Immutable, timestamped record of a consent decision (nLPD/GDPR proof).
    Works for both anonymous visitors (consent_id cookie) and logged-in users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "accounts.Customer", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="consent_logs",
    )
    consent_id = models.CharField(max_length=64, db_index=True,
        help_text="Anonymous consent identifier stored in the cookie")
    necessary = models.BooleanField(default=True)   # always true (informational)
    analytics = models.BooleanField(default=False)
    marketing = models.BooleanField(default=False)
    policy_version = models.CharField(max_length=20, default="1.0")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consent_logs"
        ordering = ["-created_at"]