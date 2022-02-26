from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from context.models import SearchContext
from common.tests import create_user


class ContextListViewTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')
        self.context = SearchContext.objects.create(name='a search context', code='a-search-context', owner=self.user)

    def test_endpoint(self):
        response = self.client.get(f'/contexts/{self.context.code}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.context.code, html=True)

    def test_page_name(self):
        self.assertEqual(f'/contexts/{self.context.code}/', reverse('contexts-detail', args=[self.context.code]))

    def test_page_template(self):
        response = self.client.get(reverse('contexts-detail', args=[self.context.code]))
        self.assertTemplateUsed(response, template_name='context/detail.html')
