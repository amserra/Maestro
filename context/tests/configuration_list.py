from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from context.models import SearchContext, Configuration
from common.tests import create_user


class ConfigurationListViewTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.login(email='john_smith@mail.com', password='asmartpassword1')
        self.configuration = Configuration.objects.create(search_string='search str', keywords='kw1, kw2')
        self.context = SearchContext.objects.create(name='a search context', code='a-search-context', owner=self.user, configuration=self.configuration)

    def test_endpoint(self):
        response = self.client.get(f'/contexts/{self.context.code}/configuration/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, self.configuration.search_string, html=True)

    def test_page_name(self):
        self.assertEqual(f'/contexts/{self.context.code}/configuration/', reverse('contexts-configuration-detail', args=[self.context.code]))

    def test_page_template_default(self):
        response = self.client.get(reverse('contexts-configuration-detail', args=[self.context.code]))
        self.assertTemplateUsed(response, template_name='context/configuration_detail_essential.html')

    def test_page_template_page_essential(self):
        response = self.client.get(f"{reverse('contexts-configuration-detail', args=[self.context.code])}?page=essential")
        self.assertTemplateUsed(response, template_name='context/configuration_detail_essential.html')

    def test_page_template_page_advanced(self):
        response = self.client.get(f"{reverse('contexts-configuration-detail', args=[self.context.code])}?page=advanced")
        self.assertTemplateUsed(response, template_name='context/configuration_detail_advanced.html')
