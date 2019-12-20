from django.contrib.auth import authenticate, login, logout

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from appadmin.forms import UserLoginForm

def logout_user(request):
	logout(request)
	return HttpResponseRedirect(reverse('login_user'))


def login_user(request):
	form = UserLoginForm()
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect(reverse('index'))
			else:
				return render(request, 'appadmin/login.html', {'error_message': 'Your account has been disabled'})
		else:
			return render(request, 'appadmin/login.html', {'error_message': 'Invalid login', 'form' : form})
	return render(request, 'appadmin/login.html', {'form' : form})