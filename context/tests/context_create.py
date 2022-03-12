from http import HTTPStatus
from django.urls import reverse
from context.models import SearchContext
from context.tests.tests_setup import ContextTestCase
from context.forms import SearchContextCreateForm
from django.test import override_settings


class ContextCreateFormTest(ContextTestCase):
    """
    Unit test of the context create form
    """
    def setUp(self):
        super().setUp()

    def test_context_create_success_user_owner(self):
        form = SearchContextCreateForm(self.user, data={
            'owner': self.user,
            'name': self.context_name
        })
        self.assertTrue(form.is_valid())

    def test_context_create_success_organization_owner(self):
        self.organization.membership_set.create(user=self.user, has_accepted=True)
        form = SearchContextCreateForm(self.user, data={
            'owner': self.organization,
            'name': self.context_name
        })
        self.assertTrue(form.is_valid())

    def test_context_create_fail_user_not_in_organization(self):
        form = SearchContextCreateForm(self.user, data={
            'owner': self.organization,
            'name': self.context_name
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_user_has_not_accepted(self):
        self.organization.membership_set.create(user=self.user, has_accepted=False)
        form = SearchContextCreateForm(self.user, data={
            'owner': self.organization,
            'name': self.context_name
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_user_blocked(self):
        self.organization.membership_set.create(user=self.user, has_accepted=True, is_blocked=True)
        form = SearchContextCreateForm(self.user, data={
            'owner': self.organization,
            'name': self.context_name
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_user_creating_not_user(self):
        form = SearchContextCreateForm(self.user, data={
            'owner': self.other_user,
            'name': self.context_name
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_no_name(self):
        form = SearchContextCreateForm(self.user, data={
            'owner': self.user,
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_no_owner(self):
        form = SearchContextCreateForm(self.user, data={
            'name': self.context_name
        })
        self.assertFalse(form.is_valid())

    def test_context_create_fail_no_fields(self):
        form = SearchContextCreateForm(self.user, data={
        })
        self.assertFalse(form.is_valid())


class ContextCreateViewTests(ContextTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(email=self.user.email, password=self.password)

    def test_endpoint(self):
        response = self.client.get('/contexts/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_name(self):
        self.assertEqual('/contexts/new/', reverse('contexts-new'))

    def test_page_template(self):
        response = self.client.get(reverse('contexts-new'))
        self.assertTemplateUsed(response, template_name='context/create.html')

    def test_post_success(self):
        response = self.client.post(reverse('contexts-new'), data={
            'name': self.context_name,
            'owner': self.user
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_error(self):
        response = self.client.post(reverse('contexts-new'), data={
            'name': self.context_name,
        })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'This field is required.', html=True)


class ContextCreateTest(ContextTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(email=self.user.email, password=self.password)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_context_create(self):
        response = self.client.post(reverse('contexts-new'), data={
            'name': self.context_name,
            'owner': self.user
        })

        context = SearchContext.objects.get(name=self.context_name)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(context)
        self.assertEqual(context.owner, self.user)
        self.assertEqual(context.code, self.context_name.replace(' ', '-').lower())
