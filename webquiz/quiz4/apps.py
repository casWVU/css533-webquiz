from django.apps import AppConfig

class Quiz4Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quiz4'

    def ready(self):
        import quiz4.signals  # noqa
