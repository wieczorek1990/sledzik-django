from django.db import models


class NanosecondDateTimeField(models.DateTimeField):
    """Compatibility stub for migration 0002; new models use DateTimeField."""
