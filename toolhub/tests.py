from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch
from .models import CustomUser
from django.core.files.storage import FileSystemStorage



class CustomUserModelTests(TestCase):
    def setUp(self):
        CustomUser._meta.get_field('profile_picture').storage = FileSystemStorage()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role='patron'
        )

    @patch('django.core.files.storage.default_storage.delete')
    @patch('django.core.files.storage.default_storage.exists')
    def test_profile_picture_update_deletes_old_file(self, mock_exists, mock_delete):
        """
        When updating the profile picture to a new file and the old picture is not default,
        the old file should be deleted.
        """
        mock_exists.return_value = True

        initial_image = SimpleUploadedFile(
            "old_image.jpg",
            b"old image content",
            content_type="image/jpeg"
        )
        self.user.profile_picture = initial_image
        self.user.save()
        old_image_name = self.user.profile_picture.name

        new_image = SimpleUploadedFile(
            "new_image.jpg",
            b"new image content",
            content_type="image/jpeg"
        )
        self.user.profile_picture = new_image
        self.user.save()

        mock_exists.assert_called_with(old_image_name)
        mock_delete.assert_called_with(old_image_name)

    @patch('django.core.files.storage.default_storage.delete')
    @patch('django.core.files.storage.default_storage.exists')
    def test_profile_picture_update_no_deletion_when_same(self, mock_exists, mock_delete):
        """
        If the profile picture remains unchanged, no deletion should occur.
        """
        mock_exists.return_value = True

        test_image = SimpleUploadedFile(
            "image.jpg",
            b"image content",
            content_type="image/jpeg"
        )
        self.user.profile_picture = test_image
        self.user.save()


        self.user.profile_picture = self.user.profile_picture
        self.user.save()


        mock_delete.assert_not_called()



    def test_profile_picture_url_property(self):
        """
        Test that the profile_picture_url property returns the correct URL,
        whether a profile picture is set or not.
        """
        image = SimpleUploadedFile(
            "image.jpg",
            b"image content",
            content_type="image/jpeg"
        )
        self.user.profile_picture = image
        self.user.save()
        expected_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{self.user.profile_picture.name}"
        self.assertEqual(self.user.profile_picture_url, expected_url)

        self.user.profile_picture = None
        self.user.save()
        default_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/profile_pictures/default.png"
        self.assertEqual(self.user.profile_picture_url, default_url)


class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patron_user = CustomUser.objects.create_user(
            username='patron',
            email='patron@example.com',
            password='pass123',
            role='patron'
        )
        self.librarian_user = CustomUser.objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='pass123',
            role='librarian'
        )

    def test_patron_home_template(self):
        self.client.login(username='patron', password='pass123')
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, "toolhub/patron_home.html")
        self.assertEqual(response.context['user'].role, 'patron')

    def test_librarian_home_template(self):
        self.client.login(username='librarian', password='pass123')
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, "toolhub/librarian_home.html")
        self.assertEqual(response.context['user'].role, 'librarian')


