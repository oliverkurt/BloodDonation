from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Profile


def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        if user is not None:
            if hasattr(user, 'profile'):
                login(request, user)
                return redirect('homepage')  # Change to your homepage URL
            else:
                messages.warning(request, 'Please complete your profile.')
                return redirect('profile_create')  # Redirect to profile creation form
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'registration/login.html')

def create_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect('homepage')
    else:
        form = ProfileForm()

    if request.method == 'GET' and 'region' in request.GET:
        form.set_provinces(request.GET.get('region'))
    if request.method == 'GET' and 'province' in request.GET:
        form.set_municipalities(request.GET.get('province'))

    return render(request, 'profile/create_profile.html', {'form': form})

from django.shortcuts import render, get_object_or_404
from .models import Profile, BloodDonationRequest

def view_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    donation_requests = BloodDonationRequest.objects.filter(user=request.user)

    return render(request, 'profile/view_profile.html', {
        'profile': profile,
        'donation_requests': donation_requests,
    })

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm
from django.utils import timezone
from datetime import timedelta

class UpdateProfileView(View):
    template_name = 'profile/update_profile.html'

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        form = ProfileForm(instance=profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        form = ProfileForm(request.POST, instance=profile)

        if form.is_valid():
            availability_changed = form.cleaned_data['availability'] != profile.availability

            if availability_changed and form.cleaned_data['availability']:
                last_donation_date = profile.last_donation_date
                if last_donation_date:
                    days_since_last_donation = (timezone.now().date() - last_donation_date).days
                    if days_since_last_donation < 56:
                        remaining_days = 56 - days_since_last_donation
                        messages.error(request,
                                       f"You must wait {remaining_days} more days before you can change your availability.")
                        return render(request, self.template_name, {'form': form})

            form.cleaned_data['blood_type'] = profile.blood_type  # Prevent changing blood type
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('view_profile')

        return render(request, self.template_name, {'form': form})

from django.views import View
from django.shortcuts import render, redirect
from .models import BloodDonationRequest

class BloodDonationRequestView(View):
    def get(self, request):
        return render(request, 'blood_donation_form.html')

    def post(self, request):
        if availability is False and request.POST['request_type'] == 'donating':
            return redirect('error_page')  # Redirect if user is not available

        blood_donation_request = BloodDonationRequest(
            user=request.user,
            request_type=request.POST['request_type'],
            blood_type=request.POST['blood_type'] if request.POST['request_type'] == 'receiving' else request.user.profile.blood_type,
            region=request.POST['region'] if request.POST['request_type'] == 'receiving' else request.user.profile.region,
            province=request.POST['province'] if request.POST['request_type'] == 'receiving' else request.user.profile.province,
            municipality=request.POST['municipality'] if request.POST['request_type'] == 'receiving' else request.user.profile.municipality,
        )
        blood_donation_request.save()
        return redirect('view_profile')

    from django.views import View
    from django.shortcuts import render, redirect, get_object_or_404
    from .models import BloodDonationRequest

    class EditBloodDonationRequestView(View):
        def get(self, request, pk):
            donation_request = get_object_or_404(BloodDonationRequest, pk=pk, user=request.user,
                                                 request_type='receiving')
            return render(request, 'edit_blood_donation_request.html', {'donation_request': donation_request})

        def post(self, request, pk):
            donation_request = get_object_or_404(BloodDonationRequest, pk=pk, user=request.user,
                                                 request_type='receiving')
            donation_request.blood_type = request.POST['blood_type']
            donation_request.region = request.POST['region']
            donation_request.province = request.POST['province']
            donation_request.municipality = request.POST['municipality']
            donation_request.save()
            return redirect('view_profile')

        class DeleteBloodDonationRequestView(View):
            def post(self, request, pk):
                donation_request = get_object_or_404(BloodDonationRequest, pk=pk, user=request.user)
                donation_request.delete()
                return redirect('view_profile')

            from django.views.generic import ListView

            class BloodDonationRequestListView(ListView):
                model = BloodDonationRequest
                template_name = 'blood_donation_request_list.html'
                context_object_name = 'requests'

                def get_queryset(self):
                    return BloodDonationRequest.objects.filter(user=self.request.user)

                from django.views.generic import DetailView

                class BloodDonationRequestDetailView(DetailView):
                    model = BloodDonationRequest
                    template_name = 'blood_donation_request_detail.html'
                    context_object_name = 'request'

                    def get_context_data(self, **kwargs):
                        context = super().get_context_data(**kwargs)
                        context['profile'] = self.object.user.profile  # Include the user's profile information
                        return context

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from .models import BloodDonationRequest
from django.contrib.auth.models import User

class AdminBloodDonationRequestView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        requests = BloodDonationRequest.objects.all()
        return render(request, 'admin_blood_donation_requests.html', {'requests': requests})

class AdminEditUserView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, 'edit_user.html', {'user': user})

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.username = request.POST['username']
        user.is_active = request.POST.get('is_active', True)
        user.save()
        return redirect('admin_user_list')





