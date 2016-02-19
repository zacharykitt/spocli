import requests, base64, datetime, time, urllib, sys, os, argparse

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

class Browse(object):
	def featured_playlists(user):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/browse/featured-playlists'
		user_params = user.get_base_params()
		res = requests.get(url, headers=user.session.header, params=user_params)
		featured_playlist_dict = res.json()
		for item in featured_playlist_dict['playlists']['items']:
			print('title: {0: <50} | uri: {1}'.format(item['name'], item['uri']))

class Search(object):
	def find_artists(user, query):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/search'
		endpoint_params = {'q': query, 'type': 'artist', 'limit': 5}
		res = requests.get(url, headers=user.session.header, params=endpoint_params)
		print(endpoint_params)
		search_result_dict = res.json()
		for item in search_result_dict['artists']['items']:
			print('name: {0: <51} | id: {1}'.format(item['name'], item['id']))

class Artist(object):
	def list_albums(user, artist_id):
		user.session.is_token_valid()
		url = 'https://api.spotify.com/v1/artists/{0}/albums'.format(artist_id)
		endpoint_params = {'album_type': 'album', 'market': 'US'}
		res = requests.get(url, headers=user.session.header, params=endpoint_params)
		album_dict = res.json()
		for item in album_dict['items']:
			print('name: {0: <51} | id: {1}'.format(item['name'], item['uri']))		


parser = argparse.ArgumentParser(description='Access the Spotify API from the command line.')
#parser.add_argument('--res', nargs='?', help='Select which API resource to interact with.',					
#choices=['albums', 'artists', 'browse', 'search', 'playlists'])
subparsers = parser.add_subparsers(help='Learn more about the various API categories.', dest='category')

parser_artists = subparsers.add_parser('artists', help='Interact with the Artists resource.')
parser_artists.add_argument('--id', nargs='?', help='The Spotify artist ID.', required=True)
parser_artists.add_argument('--endpoint', nargs='?', help='Select the resource\'s endpoint.',
					choices=['related', 'albums'])

parse_search = subparsers.add_parser('search', help='Search for artists, albums, and tracks.')
parse_search.add_argument('--q', nargs='?', help='The search query.', required=True)
parse_search.add_argument('--type', nargs='?', help="The resource to search through.",
					choices=['album', 'artist', 'track'])

args = parser.parse_args()

user = User()

if args.category == 'artists':
	if args.endpoint == 'related':
		pass
	else:
		Artist.list_albums(user, args.id)
elif args.category == 'browse':
	pass
elif args.category == 'search':
	if args.type == 'artist':
		Search.find_artists(user, args.q)
else:
	pass