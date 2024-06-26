import json
from pprint import pprint

import requests
from requests.exceptions import Timeout
from flask import abort

from app import app
# -------------------------------------------------------------------------------------------------

BASE_API_URL = "https://api.spotify.com/v1"
bad_response = 'Received a response from Spotify but'

def _get(session, endpoint=None, url=None, **params):
	from spotify_access_token import get_access_token
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

# -------------------------------------------------------------------------------------------------
MARKET = app.config['MARKET']

def get_artist_data(artist_id):
	session = requests.Session()

	endpoint = f"/artists/{artist_id}"
	data = _get(session, endpoint)

	artist_data = {
		'name': data['name'],
		'total_playcount': 0,
		'popularity_index': str(data['popularity']),
		'image_url': None,
		'spotify_url': data['external_urls']['spotify'],
		'albums': [],
		'compilations': [],
		'singles': []
	}
	if artist_images := data['images']:
		artist_data['image_url'] = artist_images[0]['url']

	total_albums = 0
	for album_type in ('album', 'compilation', 'single'):
		endpoint = f"/artists/{artist_id}/albums"
		params = {
			'include_groups': album_type,
			'market': MARKET,
			'limit': 50,
			'offset': 0
		}
		data = _get(session, endpoint, **params)

		album_id_list = [item['id'] for item in data['items']]

		while data['next']:
			data = _get(session, url=data['next'])

			for item in data['items']:
				album_id_list.append(item['id'])

		start, end = 0, 20
		step = end
		while album_id_list[start:end]:
			endpoint = "/albums"
			params = {
				'ids': ','.join(album_id_list[start:end]),
				'market': MARKET
			}
			data = _get(session, endpoint, **params)

			for album in data['albums']:
				playcount = _get_album_playcount(session, album['id'])[1]

				album_data = {
					'title': album['name'],
					'total_tracks': str(album['total_tracks']),
					'total_playcount': f'{playcount:,}',
					'popularity_index': str(album['popularity']),
					'cover_art_url': album['images'][1]['url'],
					'spotify_url': album['external_urls']['spotify'],
					'id': album['id']
				}
				artist_data[f'{album_type}s'].append(album_data)
				artist_data['total_playcount'] += playcount

				print(f'Successful data retrieval for {album_data["title"]}..')

			start, end = start+step, end+step

		print(f'{album_type.title()}s:', len(album_id_list))
		total_albums += len(album_id_list)

	artist_data['total_playcount'] = f'{artist_data["total_playcount"]:,}'

	print('Total no. of releases:', total_albums)
	return artist_data

def get_album_data(album_id=None, track_id=None):
	session = requests.Session()

	if track_id:
		album_id = _get_album_id_for_track(session, track_id)

	album_playcount, total_playcount = _get_album_playcount(session, album_id)

	endpoint = f"/albums/{album_id}"
	params = {'market': MARKET}
	data = _get(session, endpoint, **params)

	album_data = {
		'name': data['name'],
		'total_playcount': f'{total_playcount:,}',
		'popularity_index': str(data['popularity']),
		'image_url': None,
		'spotify_url': data['external_urls']['spotify'],
		'artists': [],
		'tracks': [],
		'is_multi-disc': False,
		'track_highlight': track_id
	}
	if album_images := data['images']:
		album_data['image_url'] = album_images[0]['url']

	artist_id_list = [artist['id'] for artist in data['artists']]
	track_id_list = [item['id'] for item in data['tracks']['items']]

	linked_from_list = [
		item['linked_from']['id'] if item.get('linked_from') else None
		for item in data['tracks']['items']
	]

	data_next = data['tracks']['next']
	while data_next:
		data = _get(session, url=data_next)

		for item in data['items']:
			track_id_list.append(item['id'])

			if item.get('linked_from'):
				linked_from_list.append(item['linked_from']['id'])
			else:
				linked_from_list.append(None)

		data_next = data['next']

	if album_data['track_highlight']:
		for track_id, linked_from in zip(track_id_list, linked_from_list):
			if album_data['track_highlight'] == linked_from:
				album_data['track_highlight'] = track_id
				break

	endpoint = "/artists"
	params = {'ids': ','.join(artist_id_list)}
	data = _get(session, endpoint, **params)

	for artist in data['artists']:
		artist_data = {
			'name': artist['name'],
			'image_url': None,
			'spotify_url': artist['external_urls']['spotify'],
			'id': artist['id']
		}
		if artist_images := artist['images']:
			artist_data['image_url'] = artist_images[2]['url']

		album_data['artists'].append(artist_data)

	start, end = 0, 50
	step = end
	while track_id_list[start:end]:
		endpoint = "/tracks"
		params = {
			'ids': ','.join(track_id_list[start:end]),
			'market': MARKET
		}
		data = _get(session, endpoint, **params)

		for track in data['tracks']:
			title = track['name'] if track['name'] else track['uri']

			try:
				playcount = album_playcount[track['uri']]
			except KeyError:
				album_id = track['album']['id']
				album_playcount = _get_album_playcount(session, album_id)[0]

				playcount = album_playcount[track['uri']]

				endpoint = f"/albums/{album_id}"
				params = {'market': MARKET}
				data2 = _get(session, endpoint, **params)

				album_data['popularity_index'] = str(data2['popularity'])

			track_data = {
				'title': title,
				'disc_number': str(track['disc_number']),
				'track_number': str(track['track_number']),
				'playcount': f'{playcount:,}',
				'popularity_index': str(track['popularity']),
				'id': track['id']
			}
			album_data['tracks'].append(track_data)

			if track['disc_number'] > 1:
				album_data['is_multi-disc'] = True

		print(f'Successful data retrieval for {start + len(data["tracks"])} track(s)..')
		start, end = start+step, end+step

	return album_data

def get_playlist_data(playlist_id):
	session = requests.Session()

	endpoint = f"/playlists/{playlist_id}"
	params = {
		'market': MARKET,
		'fields': 'name,followers,images,external_urls'
	}
	data = _get(session, endpoint, **params)

	playlist_data = {
		'name': data['name'],
		'followers': f'{data["followers"]["total"]:,}',
		'image_url': data['images'][0]['url'],
		'spotify_url': data['external_urls']['spotify'],
		'tracks': [],
		'track_count': None
	}

	endpoint = f"/playlists/{playlist_id}/tracks"
	params = {
		'market': MARKET,
		'fields': 'next,items(track(name,popularity,id,uri,linked_from),track.artists(name,id),track.album(images,external_urls,id)',
		'limit': 100,
		'offset': 0
	}
	data = _get(session, endpoint, **params)

	playcount_data = {}
	linked_from_list = []
	local_tracks, podcast_tracks = 0, 0
	step = 0
	while True:
		for item in data['items']:
			track = item['track']

			if 'spotify:episode:' in track['uri']:
				podcast_tracks += 1
				continue

			if 'spotify:local:' in track['uri']:
				local_tracks += 1
				continue

			title = track['name'] if track['name'] else track['uri']

			if (album_id := track['album']['id']) not in playcount_data:
				playcount_data[album_id] = _get_album_playcount(session, album_id)[0]

			try:
				playcount = playcount_data[album_id][track['uri']]
			except KeyError:
				playcount = playcount_data[album_id][track['linked_from']['uri']]
				linked_from_list.append(track['id'])

			track_data = {
				'title': title,
				'playcount': f'{playcount:,}',
				'popularity_index': str(track['popularity']),
				'artists': track['artists'],
				'cover_art_url': None,
				'spotify_url': track['album']['external_urls']['spotify'],
				'id': track['id']
			}
			if album_images := track['album']['images']:
				track_data['cover_art_url'] = album_images[1]['url']

			playlist_data['tracks'].append(track_data)

		print(f'Successful data retrieval for {step*params["limit"] + len(data["items"])} track(s)..')

		if data['next']:
			data = _get(session, url=data['next'])
			step += 1
		else:
			playlist_data['track_count'] = len(playlist_data['tracks'])
			print(
				f'{podcast_tracks} podcast track(s) and '
				f'{local_tracks} local track(s) detected / excluded from table.'
			)
			break

	updated_pop_data = {}
	start, end = 0, 50
	step = end
	while linked_from_list[start:end]:
		endpoint = "/tracks"
		params = {
			'ids': ','.join(linked_from_list[start:end]),
			'market': MARKET
		}
		data = _get(session, endpoint, **params)

		for track in data['tracks']:
			updated_pop_data[track['id']] = track['popularity']

		start, end = start+step, end+step

	for track in playlist_data['tracks']:
		if track['id'] in updated_pop_data:
			track['popularity_index'] = str(updated_pop_data[track['id']])

	return playlist_data

# -------------------------------------------------------------------------------------------------
def _get_album_id_for_track(session, track_id):
	endpoint = f"/tracks/{track_id}"
	params = {'market': MARKET}
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

		track_uri, playcount = track['uri'], track['playcount']
		album_playcount[track_uri] = int(playcount)

	total_playcount = sum(album_playcount.values())

	return album_playcount, total_playcount
