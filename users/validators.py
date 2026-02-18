import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class DigitsOnlyValidator:
    """
    Validate that the password contains only digits and is at least
    `min_length` characters long.
    """

    def __init__(self, min_length=6):
        self.min_length = min_length

    def validate(self, password, user=None):
        if not password.isdigit():
            raise ValidationError(
                _("PIN must contain only digits."),
                code="password_not_digits",
            )
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"PIN must be at least {self.min_length} digits long."),
                code="password_too_short",
            )

    def get_help_text(self):
        return _(f"Your PIN must contain only digits and be at least {self.min_length} digits long.")
