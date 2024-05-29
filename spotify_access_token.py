import time, json
from os import path
from pprint import pprint

import requests
from requests.exceptions import Timeout
from flask import abort

from app import SPOTIFY_TOKEN
from spotify_web_api import _abort_from_request, bad_response
# -------------------------------------------------------------------------------------------------

ACCESS_TOKEN_URL = "https://open.spotify.com/get_access_token"

def _save_token_info():
	try:
		response = requests.get(ACCESS_TOKEN_URL, timeout=5)

	except Timeout:
		_abort_from_request(ACCESS_TOKEN_URL, is_timeout=True)
	except Exception as e:
		_abort_from_request(ACCESS_TOKEN_URL, is_timeout=False, e=e)

	response = response.json()

	if 'accessToken' not in response:
		pprint(response)
		print({'URL:', ACCESS_TOKEN_URL})

		bad_response_msg = f'{bad_response} no access token granted.'
		abort(500, description=bad_response_msg)

	token = response

	print(f'Saving new token info to "{SPOTIFY_TOKEN}"..')
	with open(SPOTIFY_TOKEN, 'w') as f:
		json.dump(token, f, indent=4)
	print('[TOKEN INFO SUCCESSFULLY SAVED]')

def _get_token_info():
	with open(SPOTIFY_TOKEN) as f:
		token = json.load(f)

	return token

def get_access_token():
	if not path.exists(SPOTIFY_TOKEN):
		_save_token_info()

	token = _get_token_info()

	now = time.time()
	if now < token['accessTokenExpirationTimestampMs'] / 1000:
		return token['accessToken']

	_save_token_info()
	access_token = _get_token_info()['accessToken']

	return access_token
