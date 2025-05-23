from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch
from .models import CustomUser, Item, Collection, BorrowRequest
from django.core.files.storage import FileSystemStorage, default_storage
import os


# Disable SSL redirect/cookie‐secure in tests
TEST_SETTINGS = {
    "SECURE_SSL_REDIRECT": False,
    "SESSION_COOKIE_SECURE": False,
    "CSRF_COOKIE_SECURE": False,
}

@override_settings(**TEST_SETTINGS)
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
        default_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/default.png"
        self.assertEqual(self.user.profile_picture_url, default_url)


@override_settings(**TEST_SETTINGS)
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
        self.assertTemplateUsed(response, "toolhub/home/home.html")
        self.assertEqual(response.context['user'].role, 'patron')

    def test_librarian_home_template(self):
        self.client.login(username='librarian', password='pass123')
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, "toolhub/home/home.html")
        self.assertEqual(response.context['user'].role, 'librarian')

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xff\xff\xff\x21\xf9\x04\x00\x00'
    b'\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x4c'
    b'\x01\x00\x3b'
)

@override_settings(**TEST_SETTINGS, MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
class ItemTests(TestCase):
    def setUp(self):
        Item._meta.get_field('image').storage = FileSystemStorage()
        self.client = Client()
        self.librarian = CustomUser.objects.create_user(
            username="librarian", email="librarian@test.com", password="pass", role="librarian"
        )
        self.patron = CustomUser.objects.create_user(
            username="patron", email="patron@test.com", password="pass", role="patron"
        )

    def tearDown(self):
        for item in Item.objects.all():
            if item.image:
                try:
                    default_storage.delete(item.image.name)
                except Exception:
                    pass

    def test_item_model_default_image_url(self):
        """
        Verify that the image_url property returns the default URL when no image is set.
        """
        item = Item.objects.create(
            name="Test Item",
            description="A test item",
            identifier="unique_item_123",
            status="available",
            location="main_warehouse",
        )
        expected_default = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/logo.png"
        self.assertEqual(item.image_url, expected_default)

    def test_item_model_with_image(self):
        """
        Verify that the image_url property returns the correct URL when an image is provided.
        """
        item = Item.objects.create(
            name="Test Item With Image",
            description="A test item with image",
            identifier="unique_item_124",
            status="available",
            location="main_warehouse",
        )
        image_file = SimpleUploadedFile("test.gif", SMALL_GIF, content_type="image/gif")
        item.image = image_file
        item.save()
        expected_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{item.image.name}"
        self.assertEqual(item.image_url, expected_url)

    def test_add_item_view_permissions(self):
        """
        Test that only librarians can add items.
        """
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("add_item"))
        self.assertEqual(response.status_code, 403)

        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("add_item"))
        self.assertEqual(response.status_code, 200)
        image_file = SimpleUploadedFile("test.gif", SMALL_GIF, content_type="image/gif")
        post_data = {
            "name": "View Test Item",
            "description": "Item created via view test",
            "identifier": "view_test_item_001",
            "status": "available",
            "location": "main_warehouse",
            "image": image_file,
        }
        response = self.client.post(reverse("add_item"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(identifier="view_test_item_001").exists())

@override_settings(**TEST_SETTINGS, MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
class CollectionTests(TestCase):
    def setUp(self):
        Collection._meta.get_field('image').storage = FileSystemStorage()
        self.client = Client()
        self.librarian = CustomUser.objects.create_user(
            username="librarian", email="librarian@test.com", password="pass", role="librarian"
        )
        self.patron = CustomUser.objects.create_user(
            username="patron", email="patron@test.com", password="pass", role="patron"
        )
        self.public_collection = Collection.objects.create(
            title="Public Collection",
            description="Public collection description",
            visibility="public",
            creator=self.librarian,
        )
        self.private_collection = Collection.objects.create(
            title="Private Collection",
            description="Private collection description",
            visibility="private",
            creator=self.librarian,
        )
        self.private_collection.allowed_users.add(self.patron)

    def tearDown(self):
        for coll in Collection.objects.all():
            if coll.image:
                try:
                    default_storage.delete(coll.image.name)
                except Exception:
                    pass

    def test_collection_model_default_image_url(self):
        """
        Verify that a collection's image_url property returns the default URL when no image is set.
        """
        collection = Collection.objects.create(
            title="Model Test Collection",
            description="Testing collection model",
            visibility="public",
            creator=self.librarian,
        )
        expected_default = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/toolhub/images/logo.png"
        self.assertEqual(collection.image_url, expected_default)

    def test_collection_model_with_image(self):
        """
        Verify that a collection's image_url property returns the correct URL when an image is provided.
        """
        collection = Collection.objects.create(
            title="Collection With Image",
            description="A collection with image",
            visibility="public",
            creator=self.librarian,
        )
        image_file = SimpleUploadedFile("collection.gif", SMALL_GIF, content_type="image/gif")
        collection.image = image_file
        collection.save()
        expected_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/{collection.image.name}"
        self.assertEqual(collection.image_url, expected_url)

    def test_add_collection_view_visibility_choices(self):
        """
        Verify that patrons can only create public collections while librarians can choose between public and private.
        """
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("add_collection"))
        form = response.context["form"]
        self.assertEqual(form.fields["visibility"].choices, [("public", "Public")])
        post_data = {
            "title": "Patron Collection",
            "description": "Collection created by patron",
            "visibility": "public",
        }
        response = self.client.post(reverse("add_collection"), post_data)
        self.assertEqual(response.status_code, 302)
        collection = Collection.objects.get(title="Patron Collection")
        self.assertEqual(collection.creator, self.patron)
        self.assertEqual(collection.visibility, "public")

        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("add_collection"))
        form = response.context["form"]
        self.assertTrue(len(form.fields["visibility"].choices) > 1)

    def test_view_collection_access(self):
        """
        Verify that public collections are accessible to all logged-in users,
        and that private collections enforce access restrictions.
        """
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("view_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("view_collection", args=[self.private_collection.uuid]))
        self.assertEqual(response.status_code, 200)

        new_patron = CustomUser.objects.create_user(
            username="new_patron", email="newpatron@test.com", password="pass", role="patron"
        )
        self.client.login(username="new_patron", password="pass")
        response = self.client.get(reverse("view_collection", args=[self.private_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("access-denied", response.url)

    def test_edit_collection_permissions(self):
        """
        Verify that only the creator of a collection can edit it.
        """
        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("edit_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 200)
        # Edit via POST.
        post_data = {
            "title": "Edited Collection",
            "description": "Edited description",
            "visibility": "public",
        }
        response = self.client.post(reverse("edit_collection", args=[self.public_collection.uuid]), post_data)
        self.assertEqual(response.status_code, 302)
        self.public_collection.refresh_from_db()
        self.assertEqual(self.public_collection.title, "Edited Collection")

        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("edit_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("access-denied", response.url)

    def test_delete_collection_permissions(self):
        """
        Verify that only the collection's creator or a librarian can delete it.
        """
        self.client.login(username="librarian", password="pass")
        response = self.client.post(reverse("delete_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(uuid=self.public_collection.uuid)

        collection = Collection.objects.create(
            title="Delete Test Collection",
            description="Test deletion",
            visibility="public",
            creator=self.librarian,
        )
        self.client.login(username="patron", password="pass")
        response = self.client.post(reverse("delete_collection", args=[collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Collection.objects.filter(uuid=collection.uuid).exists())

@override_settings(**TEST_SETTINGS)
class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.librarian = CustomUser.objects.create_user(
            username="librarian", email="librarian@test.com", password="pass", role="librarian"
        )
        self.patron = CustomUser.objects.create_user(
            username="patron", email="patron@test.com", password="pass", role="patron"
        )
        self.public_collection = Collection.objects.create(
            title="Public Collection",
            description="Public collection desc",
            visibility="public",
            creator=self.librarian,
        )
        self.private_collection = Collection.objects.create(
            title="Private Collection",
            description="Private collection desc",
            visibility="private",
            creator=self.librarian,
        )
        self.private_collection.allowed_users.add(self.patron)

    def test_add_item_view_permissions(self):
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("add_item"))
        self.assertEqual(response.status_code, 403)


        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("add_item"))
        self.assertEqual(response.status_code, 200)

        image_file = SimpleUploadedFile("test.gif", SMALL_GIF, content_type="image/gif")
        post_data = {
            "name": "View Test Item",
            "description": "Item created via view test",
            "identifier": "view_test_item_001",
            "status": "available",
            "location": "main_warehouse",
            "image": image_file,
        }
        response = self.client.post(reverse("add_item"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(identifier="view_test_item_001").exists())

    def test_add_collection_view_visibility_choices(self):
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("add_collection"))
        form = response.context["form"]
        self.assertEqual(form.fields["visibility"].choices, [("public", "Public")])
        post_data = {
            "title": "Patron Collection",
            "description": "Only public allowed",
            "visibility": "public",
        }
        response = self.client.post(reverse("add_collection"), post_data)
        self.assertEqual(response.status_code, 302)
        collection = Collection.objects.get(title="Patron Collection")
        self.assertEqual(collection.creator, self.patron)
        self.assertEqual(collection.visibility, "public")

        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("add_collection"))
        form = response.context["form"]
        self.assertTrue(len(form.fields["visibility"].choices) > 1)

    def test_view_collection_access(self):
        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("view_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("view_collection", args=[self.private_collection.uuid]))
        self.assertEqual(response.status_code, 200)

        new_patron = CustomUser.objects.create_user(
            username="new_patron", email="newpatron@test.com", password="pass", role="patron"
        )
        self.client.login(username="new_patron", password="pass")
        response = self.client.get(reverse("view_collection", args=[self.private_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("access-denied", response.url)

    def test_edit_collection_permissions(self):
        self.client.login(username="librarian", password="pass")
        response = self.client.get(reverse("edit_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 200)
        post_data = {
            "title": "Edited Collection",
            "description": "Edited description",
            "visibility": "public",
        }
        response = self.client.post(reverse("edit_collection", args=[self.public_collection.uuid]), post_data)
        self.assertEqual(response.status_code, 302)
        self.public_collection.refresh_from_db()
        self.assertEqual(self.public_collection.title, "Edited Collection")

        self.client.login(username="patron", password="pass")
        response = self.client.get(reverse("edit_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("access-denied", response.url)

    def test_delete_collection_permissions(self):
        self.client.login(username="librarian", password="pass")
        response = self.client.post(reverse("delete_collection", args=[self.public_collection.uuid]))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(Collection.DoesNotExist):
            Collection.objects.get(uuid=self.public_collection.uuid)

        collection = Collection.objects.create(
            title="Delete Test",
            description="Test deletion",
            visibility="public",
            creator=self.librarian,
        )
        self.client.login(username="patron", password="pass")
        response = self.client.post(reverse("delete_collection", args=[collection.uuid]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Collection.objects.filter(uuid=collection.uuid).exists())

@override_settings(**TEST_SETTINGS)
class BorrowViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create librarian and patron users.
        self.librarian = CustomUser.objects.create_user(
            username="lib", email="librarian@test.com", password="pass", role="librarian"
        )
        self.patron = CustomUser.objects.create_user(
            username="patron", email="patron@test.com", password="pass", role="patron"
        )
        # Create an item that is available.
        self.item = Item.objects.create(
            name="Saw",
            identifier="saw001",
            status="available",
            location="main",
            description="Hand saw",
            image="",
        )
        # Create an existing borrow request from the patron.
        self.borrow_request = BorrowRequest.objects.create(
            item=self.item,
            user=self.patron,
            status="pending",
        )

    def test_request_borrow_already_requested(self):
        """
        Verify that if a patron has a pending (or approved) request for an item,
        a duplicate borrow request is not allowed.
        """
        self.client.login(username="patron", password="pass")
        # Attempt to request borrowing the same item a second time.
        response = self.client.post(reverse("request_borrow", args=[self.item.id]), {})
        # The view should redirect back, showing a warning message.
        self.assertEqual(response.status_code, 302)
        # There should still be only one request.
        self.assertEqual(BorrowRequest.objects.filter(item=self.item, user=self.patron).count(), 1)

    def test_request_borrow_success(self):
        """
        Verify that a patron can submit a borrow request for an item they have not requested before.
        """
        # Create a new item that has not been requested yet.
        item2 = Item.objects.create(
            name="Hammer",
            identifier="hammer002",
            status="available",
            location="main",
            description="A sturdy hammer",
            image="",
        )
        self.client.login(username="patron", password="pass")
        # Submit the borrow request. (Assuming BorrowRequestForm does not require additional fields.)
        response = self.client.post(reverse("request_borrow", args=[item2.id]), {})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BorrowRequest.objects.filter(item=item2, user=self.patron).exists())

    def test_cancel_borrow_request(self):
        """
        Verify that a patron can cancel their own pending borrow request.
        """
        self.client.login(username="patron", password="pass")
        response = self.client.post(reverse("cancel_borrow_request", args=[self.borrow_request.id]))
        self.assertRedirects(response, reverse("my_borrow_requests"))
        # The borrow request should be deleted.
        self.assertFalse(BorrowRequest.objects.filter(id=self.borrow_request.id).exists())

    def test_approve_borrow(self):
        """
        Verify that a librarian can approve a pending borrow request.
        Approving should set the borrow request status to "approved" and update the item's status to "currently_borrowed".
        """
        self.client.login(username="lib", password="pass")
        response = self.client.post(reverse("approve_borrow", args=[self.borrow_request.id]))
        self.assertRedirects(response, reverse("my_borrow_requests"))
        self.borrow_request.refresh_from_db()
        self.assertEqual(self.borrow_request.status, "approved")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "currently_borrowed")

    def test_deny_borrow(self):
        """
        Verify that a librarian can deny a pending borrow request.
        Denying should set the borrow request status to "denied" and ensure the item's status remains "available".
        """
        self.client.login(username="lib", password="pass")
        response = self.client.post(reverse("deny_borrow", args=[self.borrow_request.id]))
        self.assertRedirects(response, reverse("my_borrow_requests"))
        self.borrow_request.refresh_from_db()
        self.assertEqual(self.borrow_request.status, "denied")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "available")