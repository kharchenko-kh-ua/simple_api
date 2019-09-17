"""
API Tests
"""
import mock
import os

from django.core.management import call_command
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.test import TestCase, override_settings

from rest_framework.test import APIClient

from .models import Post

User = get_user_model()
TEST_USERNAME = 'test'
TEST_USER_EMAIL = 'test@test.com'
TEST_USER_PASSWORD = 'random_pass_666'

DUMMY_MESSAGE = 'Simple text'

TEST_LIKER_USER = 'test_liker'
TEST_UNLIKER_USER = 'test_unliker'


class TestAuth(TestCase):
    def setUp(self):
        user = User.objects.create(
            username=TEST_USERNAME,
            email=TEST_USER_EMAIL
        )
        user.set_password(TEST_USER_PASSWORD)
        user.save()

        self.likers = []
        for i in range(3):
            user = User.objects.create(
                username=TEST_LIKER_USER + f'_{i}'
            )
            user.set_password(TEST_USER_PASSWORD)
            user.save()
            self.likers.append(user)

    def test_dummy(self):
        user = User.objects.first()
        self.assertTrue(user is not None)

    def test_get_jwt_token(self):
        client = APIClient()
        r = client.post('/api-token-auth/', data={
            'username': TEST_USERNAME,
            'password': TEST_USER_PASSWORD
        }, format='json')
        self.assertTrue(r.status_code == 200)

    def test_simple_auth(self):
        client = APIClient()
        self.assertTrue(client.login(username=TEST_USERNAME,
                                     password=TEST_USER_PASSWORD))
        r = client.post('/feed/post/create/', data={'message': DUMMY_MESSAGE},
                        format='json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Post.objects.first() is not None)

        client.logout()
        response = client.post('/feed/post/create/',
                               data={'message': 'One more text'},
                               format='json')
        self.assertEqual(response.status_code, 401)

    def test_self_like(self):
        client = APIClient()
        client.login(username=TEST_USERNAME, password=TEST_USER_PASSWORD)

        Post.objects.create(author_id=1, message='Whatever')

        r = client.patch('/feed/post/1/like/')
        self.assertEqual(r.status_code, 403)

        r = client.patch('/feed/post/1/unlike/')
        self.assertEqual(r.status_code, 403)

    def test_likes_and_unlikes(self):
        posts = [Post(author_id=1, message=DUMMY_MESSAGE)] * 3
        Post.objects.bulk_create(posts)

        client = APIClient()
        for i, user in enumerate(self.likers):
            self.assertTrue(client.login(
                username=user.username,
                password=TEST_USER_PASSWORD
            ))
            for j in range(i + 1):
                r = client.patch(f'/feed/post/{j + 1}/like/')
                self.assertEqual(r.status_code, 200)
            client.logout()

        expected_likes_map = {1: 3, 2: 2, 3: 1}
        likes_query = Post.objects.values('id').annotate(likes_count=Count('likes')).values('id', 'likes_count')
        actual_likes_map = {post['id']: post['likes_count'] for post in likes_query}
        self.assertEqual(actual_likes_map, expected_likes_map)

        for i, user in enumerate(self.likers):
            client = APIClient()
            client.login(username=user.username, password=TEST_USER_PASSWORD)
            r = client.patch(f'/feed/post/{i + 1}/unlike/')
            self.assertEqual(r.status_code, 200)

        expected_likes_map = {1: 2, 2: 1, 3: 0}
        likes_query = Post.objects.values('id').annotate(likes_count=Count('likes')).values('id', 'likes_count')
        actual_likes_map = {post['id']: post['likes_count'] for post in likes_query}
        self.assertEqual(actual_likes_map, expected_likes_map)

    @mock.patch('clearbit.Enrichment.find')
    @mock.patch('pyhunter.PyHunter.email_verifier')
    @override_settings(DEBUG_SIGNUP=False)
    def test_sign_up(self, mock_method_find, mock_method_verifier):
        mock_method_find.return_value = {'result': 'deliverable'}
        mock_method_verifier.return_value = {
            'person': {
                'name': {
                    'givenName': 'John',
                    'familyName': 'Smith'
                }
            }
        }
        client = APIClient()
        r = client.post('/sign-up/', data={
            'username': 'new_user',
            'email': 'new_user_email@gmail.com',
            'password': 'very_secret_password_9876'
        })
        self.assertEqual(r.status_code, 201)
        user = User.objects.get(username='new_user')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Smith')


class TestAPIBot(TestCase):
    """
    Just start command if dev server is running.
    Anyway, you have to check results manually.
    """

    def test_run_bot(self):
        config_path = os.path.join(settings.BASE_DIR, 'config.yaml')
        call_command('run_bot', '--config_path', config_path)
