# Generated by Django 5.1.6 on 2025-02-18 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_vote'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='question',
            name='expiration_date',
            field=models.DateTimeField(default=None, verbose_name='expiration date'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='question',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='question_image/'),
        ),
        migrations.AddField(
            model_name='question',
            name='short_description',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
