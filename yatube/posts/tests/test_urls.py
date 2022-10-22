from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='notauth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client1.force_login(self.user1)

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_posts_group_slug_exists(self):
        """Страница group/<slug:slug>/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test/')
        self.assertEqual(response.status_code, 200)

    def test_posts_profile_exists(self):
        """Страница profile/<str:username>/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/auth/')
        self.assertEqual(response.status_code, 200)

    def test_posts_post_id_exists(self):
        """Страница posts/<int:post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(f'/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_posts_unexisting_page_exists(self):
        """Страница unexisting_page доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_posts_create_exists(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_posts_edit_exists(self):
        """Страница /edit/ доступна только автору."""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/',
                                              follow=True)
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_url_template(self):
        """Страница /create/ использует верный шаблон."""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_url_template(self):
        """Страница /...edit/ использует верный шаблон."""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_guest_client(self):
        """Доступ неавторизованного пользователя"""
        pages: tuple = ('/create/',
                        f'/posts/{self.post.pk}/edit/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, 302)

    def test_posts_edit_exists(self):
        """Страница /edit/ доступна только автору."""
        response = self.authorized_client1.get(
            f'/posts/{self.post.author.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_add_comment_only_authuser(self):
        """Комментировать может только аторизованный пользователь"""
        form_data = {'text': 'test com'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data, folow=True)
        self.assertEqual(response.status_code, 302)
        response_guest = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data, folow=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response_guest.status_code, 302)
        self.assertRedirects(response_guest,
                             '/auth/login/?next=/posts/1/comment/')

    def test_posts_unexisting_page_exists(self):
        """Страница unexisting_page использует кастомный шаблон."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
