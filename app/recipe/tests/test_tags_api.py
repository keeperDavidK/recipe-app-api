from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagspiTests(TestCase):
    ''''''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagspiTests(TestCase):
    ''''''

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'tester@test.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='vegan')
        Tag.objects.create(user=self.user, name='dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        ''''''
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'password'
        )
        Tag.objects.create(user=user2, name='fruity')
        tag = Tag.objects.create(user=self.user, name='comeubbgn')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        '''test crreating nwe tag'''
        payload = {'name': 'Test'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        ''' test filtering tags to those assigned'''
        tag1 = Tag.objects.create(user=self.user, name='breakfast')
        tag2 = Tag.objects.create(user=self.user, name='lunch')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Eggs and beans',
            price=5.00,
            time_minutes=10
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        ''''''
        tag = Tag.objects.create(user=self.user, name='brunch')
        Tag.objects.create(user=self.user, name='dinner')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Pancakes',
            price=3.00,
            time_minutes=10
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Porridge',
            price=2.00,
            time_minutes=10
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
