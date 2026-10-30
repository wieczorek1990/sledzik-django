import time
from datetime import datetime, timedelta, timezone

from django.db import models


class NanosecondDateTimeField(models.DateTimeField):
    """Capture a creation time and its exact integer Unix nanoseconds together."""

    def pre_save(self, model_instance, add):
        if self.auto_now_add and add:
            timestamp = time.time_ns()
            seconds, nanoseconds = divmod(timestamp, 1_000_000_000)
            value = datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(
                microseconds=nanoseconds // 1000
            )
            setattr(model_instance, self.attname, value)
            model_instance.created_ns = timestamp
            return value
        return super().pre_save(model_instance, add)
