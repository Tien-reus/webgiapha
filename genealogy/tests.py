from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Article, FamilyMember


class FamilyPagesTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            username='admin',
            password='secret12345',
            is_staff=True,
        )

    def test_public_pages_load(self):
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)
        self.assertEqual(self.client.get(reverse('family_tree')).status_code, 200)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_manage_requires_admin_login(self):
        response = self.client.get(reverse('manage_members'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_family_tree_contains_member(self):
        FamilyMember.objects.create(full_name='Nguyen Van A', generation=1)
        response = self.client.get(reverse('family_tree'))
        self.assertContains(response, 'Nguyen Van A')

    def test_admin_can_create_member(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('manage_members'),
            {
                'action': 'save_member',
                'full_name': 'Nguyen Van B',
                'gender': FamilyMember.Gender.MALE,
                'generation': 2,
                'birth_year': 1990,
                'death_year': '',
                'hometown': 'Ha Noi',
                'spouse_name': '',
                'biography': 'Thong tin thu nghiem',
                'is_highlighted': 'on',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FamilyMember.objects.filter(full_name='Nguyen Van B').exists())

    def test_admin_can_create_article(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('manage_members'),
            {
                'action': 'save_article',
                'title': 'Bai viet moi',
                'content': 'Noi dung bai viet duoc hien thi o trang chu.',
                'author': 'Quan tri vien',
                'image_url': '',
                'image': SimpleUploadedFile('photo.jpg', b'fake-image-content', content_type='image/jpeg'),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Article.objects.filter(title='Bai viet moi').exists())
        self.assertTrue(Article.objects.get(title='Bai viet moi').image.name.startswith('articles/'))

    def test_about_page_shows_article(self):
        Article.objects.create(
            title='Ky niem dong ho',
            content='Noi dung bai viet ky niem cua dong ho.',
            author='Tac gia A',
            image_url='https://example.com/photo.jpg',
        )
        response = self.client.get(reverse('about'))
        self.assertContains(response, 'Ky niem dong ho')
