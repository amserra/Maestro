from http import HTTPStatus
from django.urls import reverse
from context.models import SearchContext
from context.tests.tests_setup import ContextTestCase
from context.forms import EssentialConfigurationForm


class ContextConfigureFormTest(ContextTestCase):
    """
    Unit test of the context configure form
    """
    def setUp(self):
        self.search_string = 'how to find dolphins'
        self.keywords = 'dolphin, cetaceous'
        self.data_type = 'Images'
        super().setUp()

    def test_context_configure_success(self):
        form = EssentialConfigurationForm(data={
            'search_string': self.search_string,
            'keywords': self.keywords,
            'data_type': self.data_type
        })
        self.assertTrue(form.is_valid())

    # TODO: fail cases


# class ContextConfigureViewTests(ContextTestCase):
#     def setUp(self):
#         super().setUp()
#         self.context = SearchContext.objects.create(name='search for audio', code='search-for-audio', owner=self.user)
#         self.client.login(email=self.user.email, password=self.password)
#
#     def test_endpoint(self):
#         response = self.client.get(f'{self.context.code}/configuration/update/')
#         self.assertEqual(response.status_code, HTTPStatus.OK)

    # def test_page_name(self):
    #     self.assertEqual('/contexts/new/', reverse('contexts-new'))
    #
    # def test_page_template(self):
    #     response = self.client.get(reverse('contexts-new'))
    #     self.assertTemplateUsed(response, template_name='context/create.html')
    #
    # def test_post_success(self):
    #     response = self.client.post(reverse('contexts-new'), data={
    #         'name': self.context_name,
    #         'owner': self.user
    #     })
    #     self.assertEqual(response.status_code, HTTPStatus.FOUND)
    #
    # def test_post_error(self):
    #     response = self.client.post(reverse('contexts-new'), data={
    #         'name': self.context_name,
    #     })
    #     self.assertEqual(response.status_code, HTTPStatus.OK)
    #     self.assertContains(response, 'This field is required.', html=True)
#
#
# class ContextConfigureTest(ContextTestCase):
#     def setUp(self):
#         super().setUp()
#         self.client.login(email=self.user.email, password=self.password)
#
#     def test_context_configure(self):
#         response = self.client.post(reverse('contexts-new'), data={
#             'name': self.context_name,
#             'owner': self.user
#         })
#
#         context = SearchContext.objects.get(name=self.context_name)
#         self.assertEqual(response.status_code, HTTPStatus.FOUND)
#         self.assertTrue(context)
#         self.assertEqual(context.owner, self.user)
#         self.assertEqual(context.code, self.context_name.replace(' ', '-').lower())
