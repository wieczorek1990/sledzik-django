from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("counting", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="action",
            name="order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="action",
            options={"ordering": ("funnel_id", "order", "pk")},
        ),
    ]
