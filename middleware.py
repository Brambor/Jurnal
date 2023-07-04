import requests
from django.http import HttpResponse

from entries.utils import get_client_ip
from entries.models import IPAddress, Machine

"""
class HostValidationMiddleware(object):
	def __init__(self, get_response):
		self.get_response = get_response
		# One-time configuration and initialization.

	def __call__(self, request):
		host = request.get_host()
		print("MIDDLEWARE connection from:", get_client_ip(request))
		is_host_valid = True # Perform host validation
		if is_host_valid:
			# Django will continue as usual
			return self.get_response(request)
		else:
			response = HttpResponse
			response.status_code = 403
			return response

"""
class HostValidationMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		# One-time configuration and initialization.

	def __call__(self, request):
		# Code to be executed for each request before
		# the view (and later middleware) are called.

		ip = get_client_ip(request)
		print("MIDDLEWARE connection from:", ip)
		'''
		if IPAddress.objects.filter(address=ip).count() == 0:
			print("Allowing, it is saved")
		else:
			response = HttpResponse
			response.status_code = 403
			return response
		'''

		response = self.get_response(request)

		# Code to be executed for each request/response after
		# the view is called.

		return response

