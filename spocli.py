import requests, base64, datetime, time, urllib, sys, os

class User(object):
	def __init__(self):
		self.locale = "en_US"
		self.country = "US"
		self.session = Session()

	def get_local_time(self):
			return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

	def get_base_params(self):
		return {'country': self.country, 'locale': self.locale, 'timestamp': self.get_local_time()}

class Session(object):
	def __init__(self):
		self.__get_auth_token()
		self.__set_header()


	def __get_auth_token(self):
		# API keys need to be encoded in base64
		credentials = bytes(os.environ['SPOTIFY_CREDS'], encoding='utf-8')
		encoded_credentials = base64.b64encode(credentials)

		# required body param
		data = {'grant_type': 'client_credentials'}

		# pass credentials in request header
		headers = {'Authorization': 'Basic %s' % encoded_credentials.decode('utf-8')}

		# make request to proper endpoint 
		url = "https://accounts.spotify.com/api/token"
		res = requests.post(url, headers=headers, data=data)
		
		# parse JSON response into a dictionary
		# {"access_token" str, "token_type": str, "expires_in": int}
		token_dict = res.json()

		# add a created_at value for checking expiration
		token_dict['created_at'] = int(time.time())

		self.token_dict = token_dict


	def __set_header(self):
		# set the session header used for requests
		auth_string = '{0} {1}'.format(self.token_dict['token_type'], self.token_dict['access_token'])
		self.header = {'Authorization': auth_string}	


	def is_token_valid(self):
		# get current time and leave room for error
		current = int(time.time()) + 1
		token_expiration = self.token_dict['created_at'] + 3600
		if current >= token_expiration:
			self.__get_auth_token()
			self.__set_header()

class SpotifyApi(object):
	@staticmethod
	def get_featured_playlists(user):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/browse/featured-playlists'
		user_params = user.get_base_params()
		res = requests.get(url, headers=user.session.header, params=user_params)
		featured_playlist_dict = res.json()
		return featured_playlist_dict

	@staticmethod
	def output_featured_playlists(featured_playlist_dict):
		for item in featured_playlist_dict['playlists']['items']:
			print('title: {0: <50} | uri: {1}'.format(item['name'], item['uri']))

	@staticmethod
	def artist_search(user, query):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/search'
		endpoint_params = {'q': query, 'type': 'artist', 'limit': 5}
		res = requests.get(url, headers=user.session.header, params=endpoint_params)
		search_result_dict = res.json()
		return search_result_dict

	@staticmethod
	def output_artist_search(search_result_dict):
		for item in search_result_dict['artists']['items']:
			print('name: {0: <51} | id: {1}'.format(item['name'], item['id']))

	@staticmethod
	def list_albums_by_artist(user, artist_id):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/artists/{0}/albums'.format(artist_id)
		endpoint_params = {'album_type': 'album', 'market': 'US'}
		res = requests.get(url, headers=user.session.header, params=endpoint_params)
		album_dict = res.json()
		return album_dict

	@staticmethod
	def output_albums(albums_dict):
		for item in albums_dict['items']:
			print('name: {0: <51} | id: {1}'.format(item['name'], item['uri']))		

def cli_menu():
	input_var = 5
	while input_var > 4:
		print('Search by artist name [1], list albums by artist [2], or list featured playlists [3] or quit [4].')
		input_var = int(input('Choose a number: '))
	return input_var

user = User()
x = cli_menu()

if x == 0:
	exit()
elif x == 1:
	input_var = input('Enter search term for artist: ')
	search_result_dict = SpotifyApi.artist_search(user, input_var)
	SpotifyApi.output_artist_search(search_result_dict)
elif x == 2:
	input_var = input('List albums by artist ID: ')
	albums_dict = SpotifyApi.list_albums_by_artist(user, input_var)
	SpotifyApi.output_albums(albums_dict)
elif x == 3:
	featured_playlist_dict = SpotifyApi.get_featured_playlists(user)
	SpotifyApi.output_featured_playlists(featured_playlist_dict)
else:
	exit()
