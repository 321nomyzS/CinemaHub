# Generated by Django 5.0.4 on 2024-11-25 17:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_role_alter_crewmember_birth_date_movie_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('content', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.status')),
            ],
        ),
        migrations.CreateModel(
            name='PostTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='dashboard.post')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.template')),
            ],
        ),
        migrations.CreateModel(
            name='PostTemplateTemplateField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, null=True)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.templatefield')),
                ('post_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_fields', to='dashboard.posttemplate')),
            ],
        ),
    ]
