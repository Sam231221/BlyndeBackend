from django.apps import AppConfig


class MbaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Mbase'
    
    def ready(self):
        import Mbase.signals
