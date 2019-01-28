# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import hgw_common.fields
import hgw_common.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_url', models.CharField(max_length=200, unique=True)),
                ('access_token', models.CharField(max_length=1024)),
                ('token_type', models.CharField(max_length=10)),
                ('expires_in', models.IntegerField()),
                ('expires_at', models.DateTimeField()),
                ('scope', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(default=hgw_common.models.generate_id, max_length=32)),
                ('source_id', models.CharField(max_length=32)),
                ('destination_id', models.CharField(max_length=32)),
                ('person_id', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('version', models.CharField(max_length=30)),
                ('payload', models.CharField(max_length=1000, validators=[hgw_common.fields.JSONValidator])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='profile',
            unique_together=set([('code', 'version')]),
        ),
        migrations.AddField(
            model_name='channel',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hgw_common.Profile'),
        ),
    ]
