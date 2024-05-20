import time, json, webbrowser
from os import path
from urllib.parse import urlparse
from pprint import pprint

import requests
from requests.exceptions import Timeout
from flask import Flask, render_template, request, abort
from werkzeug.exceptions import HTTPException
# -------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_pyfile("config.py")

SPOTIFY_DATA = path.join(app.root_path, app.config['SPOTIFY_DATA'])
SPOTIFY_TOKEN = path.join(app.root_path, app.config['SPOTIFY_TOKEN'])

# -------------------------------------------------------------------------------------------------
@app.route("/")
def home():
	return render_template("home.html.j2")

@app.route("/playcount")
def playcount_page():
	now = time.perf_counter()
	search_category, spotify_id = process_form_input(request.args.get('uri-input'))
	artist_page, album_page = 'Artist', 'Album'

	if search_category == 'artist':
		data = {
			'page': artist_page,
			'data': get_artist_data(spotify_id),
			'track_highlight': None		
		}
	elif search_category == 'album':
		data = {
			'page': album_page,
			'data': get_album_data(spotify_id),
			'track_highlight': None
		}
	elif search_category == 'track':
		data = {
			'page': album_page,
			'data': get_album_data(track_highlight=spotify_id),
			'track_highlight': spotify_id
		}
	print('Time taken to load data:', time.perf_counter()-now)

	with open(SPOTIFY_DATA, 'w') as f:
		json.dump(data, f, indent=4)

	track_highlight = data['track_highlight']
	page, data = data['page'], data['data']

	base_data = dict(
		name=data['name'],
		playcount=data['total_playcount'],
		popularity=data['popularity_index'],
		image_url=data['image_url'],
		spotify_url=data['spotify_url'],
		page=page
	)

	if page == 'Artist':
		return render_template("playcount-artist.html.j2",
			**base_data,
			albums=data['albums'],
			compilations=data['compilations'],
			singles=data['singles']
		)
	elif page == 'Album':
		return render_template("playcount-album.html.j2",
			**base_data,
			tracks=data['tracks'],
			is_multidisc=data['is_multi-disc'],
			track_highlight=track_highlight
		)

def process_form_input(form_input):
	if form_input in ('', None):
		abort(400, description='No input received / empty string.')

	err_msg = 'Invalid URI input, please check format!'

	if form_input.startswith('spotify:'):
		form_input = form_input.split(':')

	elif "open.spotify.com/" in form_input:
		form_input = urlparse(form_input).path.split('/')

	else:
		abort(400, description=err_msg)

	if len(form_input) != 3:
		abort(400, description=err_msg)

	search_category, spotify_id = form_input[1], form_input[2]

	if search_category in ('artist', 'album', 'track'):
		if len(spotify_id)==22 and spotify_id.isalnum():
			return search_category, spotify_id

	abort(400, description=err_msg)

# -------------------------------------------------------------------------------------------------
# Spotify Web API
BASE_API_URL = "https://api.spotify.com/v1"
bad_response = 'Received a response from Spotify but'

def _get(session, endpoint=None, url=None, **params):
	access_token = get_access_token()

	spotify_url = url if url else f'{BASE_API_URL}{endpoint}'
	session.headers.update({'Authorization': f'Bearer {access_token}'})

	try:
		response = session.get(spotify_url, params=params, timeout=5)

	except Timeout:
		_abort_from_request(spotify_url, is_timeout=True)
	except Exception as e:
		_abort_from_request(spotify_url, is_timeout=False, e=e)

	response = response.json()

	if response.get('error') or response.get('errors'):
		pprint(response)
		print({'URL': spotify_url})

		bad_response_msg = f'{bad_response} unable to retrieve music data.'
		abort(500, description=bad_response_msg)

	return response

def _abort_from_request(url, is_timeout, e=None):
	timeout_err_msg = 'Spotify took too long to respond.'
	default_err_msg = 'An error occurred while trying to get a response from Spotify.'

	err_msg = {'Error': e, 'URL': url}

	if is_timeout:
		err_msg['Error'] = timeout_err_msg
		print(err_msg)
		abort(500, description=timeout_err_msg)

	print(err_msg)
	abort(500, description=default_err_msg)

def get_artist_data(artist_id):
	session = requests.Session()

	endpoint = f"/artists/{artist_id}"
	data = _get(session, endpoint)

	artist_data = {
		'name': data['name'],
		'total_playcount': 0,
		'popularity_index': str(data['popularity']),
		'image_url': data['images'][0]['url'],
		'spotify_url': data['external_urls']['spotify'],
		'albums': [],
		'compilations': [],
		'singles': []
	}

	for album_type in ('album', 'compilation', 'single'):
		endpoint = f"/artists/{artist_id}/albums"
		params = {
			'include_groups': album_type,
			'market': None,
			'limit': 50,
			'offset': 0
		}
		data = _get(session, endpoint, **params)

		album_id_list = [item['id'] for item in data['items']]
		while True:
			if data['next']:
				data = _get(session, url=data['next'])
				for item in data['items']:
					album_id_list.append(item['id'])
			else:
				break

		start, end = 0, 20
		step = end
		while True:
			if album_id_list[start:end]:
				album_id_list_str = ','.join(album_id_list[start:end])

				endpoint = "/albums"
				params = {
					'ids': album_id_list_str,
					'market': None
				}
				data = _get(session, endpoint, **params)

				for album in data['albums']:
					playcount = _get_album_playcount(session, album['id'])[1]

					album_data = {
						'title': album['name'],
						'total_tracks': str(album['total_tracks']),
						'total_playcount': f'{playcount:,}',
						'popularity_index': str(album['popularity']),
						'cover_art_url': album['images'][0]['url'],
						'spotify_url': album['external_urls']['spotify'],
						'id': album['id']
					}
					artist_data[f'{album_type}s'].append(album_data)
					artist_data['total_playcount'] += playcount

				start, end = start+step, end+step

			else:
				break

	artist_data['total_playcount'] = f'{artist_data["total_playcount"]:,}'

	pprint(artist_data)
	return artist_data

def get_album_data(album_id=None, track_highlight=None):
	session = requests.Session()

	if track_highlight:
		album_id = _get_album_id_for_track(session, track_highlight)

	album_playcount, total_playcount = _get_album_playcount(session, album_id)

	endpoint = f"/albums/{album_id}"
	params = {'market': None}
	data = _get(session, endpoint, **params)

	album_data = {
		'name': data['name'],
		'total_playcount': f'{total_playcount:,}',
		'popularity_index': str(data['popularity']),
		'image_url': data['images'][0]['url'],
		'spotify_url': data['external_urls']['spotify'],
		'tracks': [],
		'is_multi-disc': False
	}

	track_id_list = [item['id'] for item in data['tracks']['items']]
	if data['tracks']['next']:
		data_next = data['tracks']['next']

		while True:
			data = _get(session, url=data_next)
			for item in data['items']:
				track_id_list.append(item['id'])

			if data['next']:
				data_next = data['next']
			else:
				break

	start, end = 0, 50
	step = end
	while True:
		if track_id_list[start:end]:
			track_id_list_str = ','.join(track_id_list[start:end])

			endpoint = "/tracks"
			params = {
				'ids': track_id_list_str,
				'market': None
			}
			data = _get(session, endpoint, **params)

			for track in data['tracks']:
				playcount = album_playcount[track['name']]

				track_data = {
					'title': track['name'],
					'disc_number': str(track['disc_number']),
					'track_number': str(track['track_number']),
					'playcount': f'{playcount:,}',
					'popularity_index': str(track['popularity']),
					'id': track['id']
				}
				album_data['tracks'].append(track_data)

				if int(track_data['disc_number']) > 1:
					album_data['is_multi-disc'] = True

			start, end = start+step, end+step

		else:
			break

	pprint(album_data)
	return album_data

def _get_album_id_for_track(session, track_id):
	endpoint = f"/tracks/{track_id}"
	params = {'market': None}
	data = _get(session, endpoint, **params)

	return data['album']['id']

def _get_album_playcount(session, album_id):
	url = "https://api-partner.spotify.com/pathfinder/v1/query"
	params = {
		'operationName': 'queryAlbumTracks',
		'variables': json.dumps({
			'uri': f'spotify:album:{album_id}',
			'offset': 0,
			'limit': 999
		}),
		'extensions': json.dumps({
			'persistedQuery': {
				'version': 1,
				'sha256Hash': '3ea563e1d68f486d8df30f69de9dcedae74c77e684b889ba7408c589d30f7f2e'
			}
		})
	}
	data = _get(session, url=url, **params)

	album_playcount = {}

	for item in data['data']['album']['tracks']['items']:
		track = item['track']
		title, playcount = track['name'], track['playcount']
		album_playcount[title] = int(playcount)

	total_playcount = sum(album_playcount.values())

	return album_playcount, total_playcount

# -------------------------------------------------------------------------------------------------
# Spotify Access Token
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
		print('URL:', ACCESS_TOKEN_URL)

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

# -------------------------------------------------------------------------------------------------
# Error handling
@app.errorhandler(HTTPException)
def handle_error(err):
	return render_template("errorhandler.html.j2",
		err_code=err.code,
		err_name=err.name,
		err_msg=err.description
	), err.code

# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	webbrowser.open(f"http://{app.config['HOST']}:{app.config['PORT']}")
	app.run(
		host=app.config['HOST'],
		port=app.config['PORT'],
	)
