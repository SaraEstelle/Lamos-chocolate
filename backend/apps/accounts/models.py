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
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


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


class Customer(AbstractBaseUser):
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

    # Statut
    is_active = models.BooleanField(
        default=True,
        help_text="Le compte est-il actif ? (False = compte suspendu)"
    )

    is_staff = models.BooleanField(
        default=False,
        help_text="Accès à l'interface admin (/admin/)"
    )

    is_superuser = models.BooleanField(
        default=False,
        help_text="Accès complet à Django admin"
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
    - Expiration : 24h (après c'est invalid)
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

    # Expiration (24h)
    expires_at = models.DateTimeField(
        help_text="Date d'expiration du token (24h)"
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