from django.test import TestCase
from django.contrib.auth import get_user_model

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    '''return recipe detail url'''
    return reverse('recipe:recipe-detail', args=[recipe_id])

def sample_tag(user, name='Main course'):
    '''create and return a sample tag'''
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='cinnamon'):
    '''create and return a sample ingredient'''
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    '''create and return a sample recipe'''
    defaults = {
        'title': 'sample recipe',
        'time_minutes': '10',
        'price': '5.00'
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    '''test unauthenticated users access'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''login req'''
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    ''' test authenticsated user access'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'tester@test.com',
            'password'
        )
        self.client.force_authenticate(self.user)

    def test_retreive_ingredient_list(self):
        '''tests getting list of recipes'''

        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''test recipes are limited to the authenticated user'''
        user2 = get_user_model().objects.create_user(
            'tester2@test.com',
            'password'
        )
        sample_recipe(user=user2)

        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        '''viewing a recipe detail'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)