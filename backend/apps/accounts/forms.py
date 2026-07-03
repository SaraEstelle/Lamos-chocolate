"""
apps/accounts/forms.py
======================
Authentication forms for user registration, login, and password reset.

Responsibilities:
1. RegisterForm — Validate user registration
2. LoginForm — Validate user login
3. PasswordResetForm — Validate password reset request
4. PasswordResetConfirmForm — Validate new password

Security:
- Server-side validation (not just JavaScript)
- No plaintext password display
- Email uniqueness validation
- Password complexity requirements
"""

from django import forms
from django.contrib.auth import authenticate

from apps.accounts.models import Customer


class RegisterForm(forms.ModelForm):
    """
    User registration form.

    Creates a new Customer with:
    - email (unique)
    - password (automatically hashed)
    - first_name, last_name, phone (optional)

    Validation:
    - Email must be unique in DB
    - Password >= 12 chars
    - Password must contain uppercase, lowercase, digits, special chars
    - Password must match confirmation
    """

    # Password field 1 (hidden)
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Minimum 12 characters",
                "autocomplete": "off",
            }
        ),
        min_length=12,
        help_text=(
            "Minimum 12 characters with uppercase, lowercase,"
            "digits and special characters",
        ),
    )

    # Password field 2 (confirmation)
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repeat your password",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = Customer
        fields = ("email", "first_name", "last_name", "preferred_language")
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "field-input", "placeholder": "your@email.ch"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "John"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "Doe"}
            ),
            "preferred_language": forms.Select(attrs={"class": "field-input"}),
        }

    def clean_email(self):
        """Check that email is unique."""
        email = self.cleaned_data.get("email")

        if Customer.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already in use. Please log in or use another email."
            )

        return email

    def clean_password(self):
        """Check password complexity."""
        password = self.cleaned_data.get("password")

        if not password:
            return password

        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            raise forms.ValidationError(
                "Password must contain at least one uppercase, one lowercase, "
                "one digit and one special character."
            )

        return password

    def clean(self):
        """Check that both passwords match."""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("The two passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        """Save the Customer with hashed password."""
        customer = super().save(commit=False)

        # Hash the password automatically
        customer.set_password(self.cleaned_data["password"])

        if commit:
            customer.save()

        return customer


class LoginForm(forms.Form):
    """
    User login form.

    Fields:
    - email (EmailField)
    - password (PasswordInput)
    - remember_me (optional) — Stay logged in
    """

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "your@email.ch",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your password",
                "autocomplete": "current-password",
            }
        ),
    )

    remember_me = forms.BooleanField(
        label="Stay logged in for 2 weeks",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):
        """Check that email and password are correct."""
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            # Try to authenticate
            customer = authenticate(username=email, password=password)

            if customer is None:
                raise forms.ValidationError("Incorrect email or password.")

            # Store the customer for the view
            self.customer = customer

        return cleaned_data


class PasswordResetForm(forms.Form):
    """
    Password reset request form.

    Field:
    - email (EmailField)

    Verifies that the email exists in DB.
    """

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "your@email.ch"}
        ),
    )

    def clean_email(self):
        """Check that the email exists."""
        email = self.cleaned_data.get("email")

        # Email exists?
        if not Customer.objects.filter(email=email).exists():
            # Security: don't reveal if email exists or not
            # Show generic message
            pass

        return email


class PasswordResetConfirmForm(forms.Form):
    """
    New password form (via email link).

    Fields:
    - new_password (PasswordInput)
    - new_password_confirm (PasswordInput)

    Validation: same as RegisterForm.password
    """

    new_password = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Minimum 12 characters",
                "autocomplete": "off",
            }
        ),
        min_length=12,
    )

    new_password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repeat your password",
                "autocomplete": "off",
            }
        ),
    )

    def clean_new_password(self):
        """Check complexity."""
        password = self.cleaned_data.get("new_password")

        if not password:
            return password

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            raise forms.ValidationError(
                "Password must contain at least one uppercase, one lowercase, "
                "one digit and one special character."
            )

        return password

    def clean(self):
        """Check that both passwords match."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if new_password and new_password_confirm:
            if new_password != new_password_confirm:
                raise forms.ValidationError("The two passwords do not match.")

        return cleaned_data


class ProfileForm(forms.ModelForm):
    """
    Form to edit a customer's own profile.

    Email is intentionally NOT editable here (changing the login identifier
    should go through a dedicated, verified flow — out of scope for now).
    """

    class Meta:
        model = Customer
        fields = (
            "first_name",
            "last_name",
            "phone",
            "npa",
            "canton",
            "preferred_language",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "field-input"}),
            "last_name": forms.TextInput(attrs={"class": "field-input"}),
            "phone": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "+41 (XX) XXX XX XX"}
            ),
            "npa": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "1201"}
            ),
            "canton": forms.Select(attrs={"class": "field-input"}),
            "preferred_language": forms.Select(attrs={"class": "field-input"}),
        }


class PasswordChangeForm(forms.Form):
    """Logged-in password change: requires the current password."""

    current_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(
            attrs={"class": "field-input", "autocomplete": "current-password"}
        ),
    )
    new_password = forms.CharField(
        label="New password",
        min_length=12,
        widget=forms.PasswordInput(
            attrs={"class": "field-input", "autocomplete": "new-password"}
        ),
    )
    new_password_confirm = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(
            attrs={"class": "field-input", "autocomplete": "new-password"}
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pwd = self.cleaned_data["current_password"]
        if not self.user or not self.user.check_password(pwd):
            raise forms.ValidationError("Your current password is incorrect.")
        return pwd

    def clean_new_password(self):
        p = self.cleaned_data.get("new_password", "")
        checks = [
            any(c.isupper() for c in p),
            any(c.islower() for c in p),
            any(c.isdigit() for c in p),
            any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p),
        ]
        if not all(checks):
            raise forms.ValidationError(
                "Password must contain uppercase, lowercase, digit"
                "and special character."
            )
        return p

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") and cleaned.get("new_password_confirm"):
            if cleaned["new_password"] != cleaned["new_password_confirm"]:
                raise forms.ValidationError("The two new passwords do not match.")
        return cleaned
