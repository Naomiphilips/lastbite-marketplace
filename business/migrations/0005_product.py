# Generated migration for Product model

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('business', '0004_listing_end_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
                ('image', models.FileField(blank=True, null=True, upload_to='products/')),
                ('notes', models.TextField(blank=True, help_text='Internal notes (not shown to customers)')),
                ('base_price', models.DecimalField(decimal_places=2, help_text='Base/starting price', max_digits=10)),
                ('min_price', models.DecimalField(blank=True, decimal_places=2, help_text='Minimum price for dynamic pricing (cannot go below this)', max_digits=10, null=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('listed', 'Listed'), ('reserved', 'Reserved'), ('sold', 'Sold'), ('expired', 'Expired')], default='draft', max_length=20)),
                ('pricing_type', models.CharField(choices=[('static', 'Static Price'), ('time_based', 'Time-Based Discount'), ('auction', 'Auction/Barter')], default='static', max_length=20)),
                ('ready_after', models.DateTimeField(blank=True, help_text='When the product becomes available', null=True)),
                ('pickup_by', models.DateTimeField(blank=True, help_text='Deadline for pickup (used for dynamic pricing)', null=True)),
                ('end_time', models.DateTimeField(blank=True, help_text='End time for dynamic pricing discounts', null=True)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=50)),
                ('zip_code', models.CharField(blank=True, max_length=10)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['status', 'pricing_type'], name='business_pr_status_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['owner', 'status'], name='business_pr_owner_i_abc123_idx'),
        ),
    ]