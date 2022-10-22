from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='отредактированный текст поста',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Test Valid form saves a post in DB"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        posts_count = Post.objects.count()
        form_data = {'text': 'test',
                     'group': self.group.pk,
                     'image': uploaded}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.post.author})
                             )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='Тестовый пост',
                                            author=self.post.author,
                                            group=self.post.pk).exists())
        self.assertEqual(response.context.get('page_obj')[0].image.name,
                         self.post.image.name)

    def test_edit_post(self):
        """Test post save after edit"""
        self.post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.group)
        old_text = self.post
        self.group2 = Group.objects.create(title='Тестовая группа2',
                                           slug='test-group',
                                           description='Описание')
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group2.pk}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_text.pk}),
            data=form_data)
        self.assertTrue(Post.objects.filter(
                        group=self.group2.pk,
                        author=self.user,
                        pub_date=self.post.pub_date
                        ).exists())
        self.assertEqual(response.status_code, 302)
