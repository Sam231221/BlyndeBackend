from django.db.models.signals import pre_save
from django.contrib.auth.models import User


#Every time email is updated, update username with that email.
def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != '':
        user.username = user.email


pre_save.connect(updateUser, sender=User)
