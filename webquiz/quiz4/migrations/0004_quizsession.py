# Generated by Django 5.0.4 on 2024-04-19 00:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz4', '0003_remove_quizlog_question_filename'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_limit', models.IntegerField()),
                ('num_questions', models.IntegerField()),
            ],
        ),
    ]
