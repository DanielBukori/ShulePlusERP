from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from shule_core.models import School


class SchoolRegistrationApprovalTests(TestCase):
    def registration_data(self):
        return {
            'name': 'Pending School',
            'subdomain': 'pendingschool',
            'school_level': 'B',
            'email': 'school@example.com',
            'phone': '255700000010',
            'primary_color': '#123456',
            'headmaster_username': 'pending-headmaster',
            'headmaster_password': 'Secure!RequestPass2026',
            'headmaster_phone': '255700000011',
            'headmaster_email': 'headmaster@example.com',
        }

    def submit_registration(self):
        return self.client.post(
            reverse('shule_core:register_school'),
            self.registration_data(),
        )

    def test_registration_stays_pending_until_admin_approves_it(self):
        response = self.submit_registration()
        self.assertRedirects(response, reverse('shule_core:registration_received'))
        school = School.objects.get(subdomain='pendingschool')
        headmaster = get_user_model().objects.get(username='pending-headmaster')

        self.assertFalse(school.is_approved)
        self.assertFalse(headmaster.is_active)
        self.assertTrue(headmaster.school_registration_pending)
        self.assertFalse(headmaster.must_change_password)
        self.assertFalse(headmaster.is_staff)
        self.assertNotIn('_auth_user_id', self.client.session)

        hidden_tenant = self.client.get(
            reverse('accounts:login'),
            HTTP_HOST='pendingschool.localhost',
        )
        self.assertEqual(hidden_tenant.status_code, 404)

        admin_user = get_user_model().objects.create_superuser(
            username='platform-admin',
            email='platform-admin@example.com',
            password='Admin!RequestPass2026',
        )
        self.client.force_login(admin_user)
        approved = self.client.post(
            reverse('admin:shule_core_school_changelist'),
            {
                'action': 'approve_pending_registrations',
                '_selected_action': [school.pk],
                'index': 0,
            },
        )

        self.assertEqual(approved.status_code, 302)
        school.refresh_from_db()
        headmaster.refresh_from_db()
        self.assertTrue(school.is_approved)
        self.assertTrue(headmaster.is_active)
        self.assertFalse(headmaster.school_registration_pending)

        self.client.logout()
        available_tenant = self.client.get(
            reverse('accounts:login'),
            HTTP_HOST='pendingschool.localhost',
        )
        self.assertEqual(available_tenant.status_code, 200)

    def test_weak_headmaster_password_is_rejected(self):
        data = self.registration_data()
        data['headmaster_password'] = 'password'

        response = self.client.post(reverse('shule_core:register_school'), data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('headmaster_password', response.context['form'].errors)
        self.assertFalse(School.objects.filter(subdomain='pendingschool').exists())


class TenantUserIsolationTests(TestCase):
    def test_school_user_cannot_access_another_schools_subdomain(self):
        school = School.objects.create(
            name='Tenant One',
            subdomain='tenantone',
            email='tenantone@example.com',
            phone='255700000051',
        )
        other_school = School.objects.create(
            name='Tenant Two',
            subdomain='tenanttwo',
            email='tenanttwo@example.com',
            phone='255700000052',
        )
        user = get_user_model().objects.create_user(
            username='tenant-one-user',
            email='tenant-one-user@example.com',
            password='test-password',
            role='HEADMASTER',
            school=school,
            must_change_password=False,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse('accounts:login'),
            HTTP_HOST=f'{other_school.subdomain}.localhost',
        )

        self.assertEqual(response.status_code, 403)
