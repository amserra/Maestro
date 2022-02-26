from http import HTTPStatus

from context.models import SearchContext
from context.tests import ContextTestCase
from django.shortcuts import reverse


class ContextDeleteTests(ContextTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(email=self.user.email, password=self.password)

    def test_endpoint(self):
        response = self.client.get(f'/contexts/{self.context.code}/delete/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_name(self):
        self.assertEqual(f'/contexts/{self.context.code}/delete/', reverse('contexts-delete', args=[self.context.code]))

    def test_delete_success(self):
        response = self.client.get(reverse('contexts-delete', args=[self.context.code]))
        self.assertFalse(SearchContext.objects.filter(code=self.context_code).exists())

    def test_delete_fail_other_user(self):
        self.client.login(email=self.other_user, password=self.password)
        response = self.client.get(reverse('contexts-delete', args=[self.context.code]))
        self.assertTrue(SearchContext.objects.filter(code=self.context_code).exists())
