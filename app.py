import time, json, webbrowser
from os import path
from urllib.parse import urlparse

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
	artist_page, album_page, playlist_page = 'Artist', 'Album', 'Playlist'

	if search_category == 'artist':
		from spotify_web_api import get_artist_data
		data = {
			'page': artist_page,
			'data': get_artist_data(spotify_id)
		}
	elif search_category == 'album':
		from spotify_web_api import get_album_data
		data = {
			'page': album_page,
			'data': get_album_data(spotify_id)
		}
	elif search_category == 'track':
		from spotify_web_api import get_album_data
		data = {
			'page': album_page,
			'data': get_album_data(track_id=spotify_id)
		}
	elif search_category == 'playlist':
		from spotify_web_api import get_playlist_data
		data = {
			'page': playlist_page,
			'data': get_playlist_data(spotify_id)
		}
	print('Time taken to load data:', round(time.perf_counter()-now, 3), 'seconds')

	with open(SPOTIFY_DATA, 'w') as f:
		json.dump(data, f, indent=4)

	page, data = data['page'], data['data']

	base_data = dict(
		name=data['name'],
		image_url=data['image_url'],
		spotify_url=data['spotify_url'],
		page=page
	)
	if page in {'Artist', 'Album'}:
		base_data.update(
			dict(
				playcount=data['total_playcount'],
				popularity=data['popularity_index']
			)
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
			artists=data['artists'],
			tracks=data['tracks'],
			is_multidisc=data['is_multi-disc'],
			track_highlight=data['track_highlight']
		)
	elif page == 'Playlist':
		return render_template("playcount-playlist.html.j2",
			**base_data,
			followers=data['followers'],
			tracks=data['tracks'],
			track_count=data['track_count']
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

	if search_category in {'artist', 'album', 'track', 'playlist'}:
		if len(spotify_id)==22 and spotify_id.isalnum():
			return search_category, spotify_id

	abort(400, description=err_msg)

# -------------------------------------------------------------------------------------------------
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
		port=app.config['PORT']
	)
