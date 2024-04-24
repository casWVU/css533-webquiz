from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission

@receiver(post_save, sender=User)
def create_superuser_group(sender, instance, created, **kwargs):
    if created:
        # Create a group if it doesn't exist
        superuser_group, created = Group.objects.get_or_create(name='SuperUser')

        # Add a permission to the group
        try:
            permission = Permission.objects.get(codename='view_quiz')
            superuser_group.permissions.add(permission)
        except ObjectDoesNotExist:
            print("Permission 'view_quiz' does not exist")

        # Add the user to the group
        superuser_group.user_set.add(instance)
