from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monapp', '0008_demandeexpert_commentaire_satisfaction_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageDiscussion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', models.TextField()),
                ('date_envoi', models.DateTimeField(auto_now_add=True)),
                ('lu', models.BooleanField(default=False)),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
                ('demande', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages_discussion', to='monapp.demandeexpert')),
            ],
            options={
                'verbose_name': 'Message de discussion',
                'verbose_name_plural': 'Messages de discussion',
                'ordering': ['date_envoi'],
            },
        ),
    ]