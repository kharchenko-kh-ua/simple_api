"""

Automated bot
To reiterate -- the purpose of the bot is to demonstrate the usage of the
    previously created REST API.
This bot should read rules from a config file (in any format you choose),
    but should have following fields
(all integers, you can rename as you see fit):
● number_of_users
● max_posts_per_user
● max_likes_per_user
Bot should read the configuration and create this activity:
● signup users (number provided in config)
● each user creates random number of posts with any content
    (up to max_posts_per_user)
After creating the signup and posting activity, posts should be liked using
    following rules:
● next user to perform a like is the user who has most posts and has not
    reached max likes
● user performs “like” activity until he reaches max likes
● user can only like random posts from users who have at least one post
    with 0 likes
● if there is no posts with 0 likes, bot stops
● users cannot like their own posts
● posts can be liked multiple times, but one user can like a certain
    post only once

"""
import os
import random
import requests
import string
import yaml

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Count

from feed.models import Post


User = get_user_model()


class Bot:
    """
    Imitate user API calls
    """
    __jwt_token = None

    @staticmethod
    def generate_name(length=10):
        return ''.join(random.choice(
            string.ascii_lowercase
        ) for i in range(length))

    @staticmethod
    def generate_password(chars=10, numbers=10):
        assert chars >= 4 and numbers >= 4
        text = ''.join(random.choice(
            string.ascii_lowercase
        ) for i in range(chars))
        numbers = ''.join(
            [str(random.choice(range(10))) for i in range(numbers)]
        )
        return text + numbers

    def generate_email(self, domain='gmail.com'):
        return f'{self.generate_name()}@{domain}'

    def register(self, username=None, email=None, password=None):
        if username is None:
            username = self.generate_name()
        if email is None:
            email = self.generate_email()
        if password is None:
            password = self.generate_password()
        r = requests.post(
            'http://localhost:8000/sign-up/',
            data={'username': username, 'email': email, 'password': password}
        )
        assert r.status_code == 201
        self.login(username, password)
        return username

    def login(self, username, password):
        """
        Obtain and save token
        """
        r = requests.post(
            'http://localhost:8000/api-token-auth/',
            data={'username': username, 'password': password},
        )
        assert r.status_code == 200
        self.__jwt_token = r.json()['token']

    def call_authorized(self, method, *args, **kwargs):
        assert self.__jwt_token is not None
        return getattr(requests, method.lower())(
            headers={
                'Authorization': 'JWT ' + self.__jwt_token
            }, *args, **kwargs
        )


class Command(BaseCommand):
    help = "Demonstrates API usage regarding to config parameters. " \
           "For example.: python manage.py run_bot -c " \
           "/home/pro_developer/config.yaml"
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_path', required=True)

    def handle(self, *args, **options):
        config_path = options['config_path']
        if not os.path.exists(config_path):
            raise CommandError('Config does not exist')

        with open(config_path) as f:
            data = yaml.load(f, Loader=yaml.Loader)
            if not isinstance(data, dict):
                raise CommandError('Config file is not correct yaml')

        keys = {'number_of_users', 'max_posts_per_user', 'max_likes_per_user'}
        if not keys.issuperset(data.keys()):
            raise CommandError('Config is not full')

        number_of_users = int(data['number_of_users'])
        max_posts_per_user = int(data['max_posts_per_user'])
        max_likes_per_user = int(data['max_likes_per_user'])

        # 1) Signup
        registered_bots = {}
        for i in range(number_of_users):
            bot = Bot()
            bot_name = bot.register()
            registered_bots[bot_name] = bot

        # 2) Create posts
        for bot_name, bot in registered_bots.items():
            posts_required = random.randint(0, max_posts_per_user)
            for i in range(posts_required):
                bot.call_authorized(
                    'post',
                    url='http://localhost:8000/feed/post/create/',
                    data={'message': 'Any text'}
                )

        # 3) Likes running
        user_order_query = User.objects.values('pk').annotate(
            post_per_user=Count('post', distinct=True),
            like_per_user=Count('like', distinct=True)
        ).order_by('-post_per_user').filter(
            like_per_user__lte=max_likes_per_user
        ).values('pk', 'username')
        for user in user_order_query:

            posts_to_like = set(User.objects.filter(
                post__likes__isnull=True
            ).exclude(post__author=user['pk']).values_list(
                'post__id', flat=True
            ))
            if len(posts_to_like) > max_likes_per_user:
                count = max_likes_per_user
            else:
                count = len(posts_to_like)

            liked = set()
            while count > 0:
                post_id = random.randint(1, max(posts_to_like))
                if post_id in liked:
                    continue

                bot = registered_bots[user['username']]
                bot.call_authorized(
                    'patch',
                    url=f'http://localhost:8000/feed/post/{post_id}/like/'
                )
                count -= 1
                liked.add(post_id)
            not_liked_posts = Post.objects.annotate(
                count=Count('likes')
            ).values('id', 'count').filter(count=0)
            if not not_liked_posts:
                break

        self.stdout.write(self.style.SUCCESS('Success!'))
