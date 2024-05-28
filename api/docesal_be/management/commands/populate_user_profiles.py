from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from docesal_be.models import UserProfile


class Command(BaseCommand):
    help = "Create UserProfile instances for existing users"

    def handle(self, *args, **kwargs):
        users_without_profile = User.objects.filter(profile__isnull=True)
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            self.stdout.write(
                self.style.SUCCESS(f"Created profile for user: {user.username}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully created profiles for all users without one."
            )
        )
