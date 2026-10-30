import counting.fields
from django.db import migrations, models


def backfill_created_ns(apps, schema_editor):
    from datetime import datetime, timezone

    ActionCounter = apps.get_model("counting", "ActionCounter")
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    counters = ActionCounter.objects.using(schema_editor.connection.alias)
    for counter in counters.all().iterator():
        delta = counter.created - epoch
        timestamp = (
            (delta.days * 86400 + delta.seconds) * 1_000_000_000
            + delta.microseconds * 1000
        )
        counters.filter(pk=counter.pk).update(created_ns=timestamp)


class Migration(migrations.Migration):
    dependencies = [("counting", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="actioncounter",
            name="created_ns",
            field=models.BigIntegerField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="actioncounter",
            name="created",
            field=counting.fields.NanosecondDateTimeField(auto_now_add=True),
        ),
        migrations.RunPython(backfill_created_ns, migrations.RunPython.noop),
    ]
