# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-20 19:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0004_auto_20161229_1703'),
    ]

    operations = [
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.TextField()),
                ('key_hash', models.BinaryField()),
            ],
            options={
                'permissions': (('can_send_registration', 'Can send a registration request.'),),
            },
        ),
    ]
