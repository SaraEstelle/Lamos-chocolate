"""Unit tests for the Customer model: password hashing and helpers."""


class TestCustomerModel:
    def test_password_is_hashed_not_stored_plaintext(self, db):
        from apps.accounts.models import Customer

        customer = Customer(
            first_name="Test", last_name="User", email="test@example.com"
        )
        customer.set_password("securepassword")
        assert customer.password_hash != "securepassword"

    def test_check_password_matches(self, db):
        from apps.accounts.models import Customer

        customer = Customer(
            first_name="Test", last_name="User", email="test@example.com"
        )
        customer.set_password("securepassword")
        assert customer.check_password("securepassword") is True

    def test_check_password_rejects_wrong_password(self, db):
        from apps.accounts.models import Customer

        customer = Customer(
            first_name="Test", last_name="User", email="test@example.com"
        )
        customer.set_password("securepassword")
        assert customer.check_password("wrongpassword") is False

    def test_full_name_property(self, db):
        from apps.accounts.models import Customer

        customer = Customer(first_name="Marie", last_name="Dupont", email="m@test.com")
        assert customer.full_name == "Marie Dupont"
