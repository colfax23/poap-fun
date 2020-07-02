# Generated by Django 3.0.7 on 2020-07-02 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20200702_1043'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField(verbose_name='order')),
                ('block_number', models.BigIntegerField(verbose_name='block number')),
                ('nonce', models.BigIntegerField(verbose_name='block nonce')),
                ('seed', models.IntegerField(blank=True, null=True, verbose_name='seed')),
            ],
            options={
                'verbose_name': 'block data',
                'verbose_name_plural': 'block data',
            },
        ),
        migrations.CreateModel(
            name='RaffleEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'raffle event',
                'verbose_name_plural': 'raffle events',
            },
        ),
        migrations.CreateModel(
            name='ResultsTable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'results table',
                'verbose_name_plural': 'results tables',
            },
        ),
        migrations.CreateModel(
            name='ResultsTableEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField(verbose_name='order')),
            ],
            options={
                'verbose_name': 'results table entry',
                'verbose_name_plural': 'results table entries',
            },
        ),
        migrations.AlterModelOptions(
            name='event',
            options={'verbose_name': 'event', 'verbose_name_plural': 'events'},
        ),
        migrations.RemoveField(
            model_name='event',
            name='poap_id',
        ),
        migrations.AddField(
            model_name='event',
            name='event_id',
            field=models.CharField(default='1', editable=False, max_length=255, verbose_name='event id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='name',
            field=models.CharField(default='name', max_length=256, verbose_name='nombre'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='participant',
            name='poap_id',
            field=models.CharField(default='1', max_length=100, verbose_name='poap id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='raffle',
            name='one_address_one_vote',
            field=models.BooleanField(default=True, verbose_name='one address one vote'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='raffle',
            name='registration_deadline',
            field=models.DateTimeField(default='2020-07-02 15:04:44.440067', verbose_name="raffle's registration deadline"),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together={('raffle', 'poap_id')},
        ),
        migrations.DeleteModel(
            name='RafflePOAP',
        ),
        migrations.AddField(
            model_name='resultstableentry',
            name='participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='results_table_entries', to='core.Participant', verbose_name='participant'),
        ),
        migrations.AddField(
            model_name='resultstableentry',
            name='results_table',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='results_table_entries', to='core.ResultsTable', verbose_name='results_table'),
        ),
        migrations.AddField(
            model_name='resultstable',
            name='raffle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='result_table', to='core.Raffle', unique=True, verbose_name='raffle'),
        ),
        migrations.AddField(
            model_name='raffleevent',
            name='event',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='event_raffles', to='core.Event', verbose_name='event'),
        ),
        migrations.AddField(
            model_name='raffleevent',
            name='raffle',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='raffle_events', to='core.Raffle', verbose_name='raffle'),
        ),
        migrations.AddField(
            model_name='blockdata',
            name='raffle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='blocks_data', to='core.Raffle', verbose_name='raffle'),
        ),
    ]
