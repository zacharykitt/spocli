import requests, base64, datetime, time, os, argparse

# the User class allows for user-header info to be passed to each API call
class User(object):
	def __init__(self):
		self.locale = "en_US"
		self.country = "US"
		self.session = Session()

	def get_local_time(self):
			return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

	def get_base_params(self):
		return {'country': self.country, 'locale': self.locale, 'timestamp': self.get_local_time()}

# the Session class allows for the management of auth tokens
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
		
		token_dict = res.json()

		# add a created_at value for checking expiration
		token_dict['created_at'] = int(time.time())

		self.token_dict = token_dict


	# set the session header used for requests
	def __set_header(self):
		auth_string = '{0} {1}'.format(self.token_dict['token_type'], self.token_dict['access_token'])
		self.header = {'Authorization': auth_string}	


	# tokens expire after 3600 s
	def is_token_valid(self):
		# get current time and leave room for error
		current = int(time.time()) + 1
		token_expiration = self.token_dict['created_at'] + 3600
		if current >= token_expiration:
			self.__get_auth_token()
			self.__set_header()

# this class was created to reduce repetition of API request code
class ApiCall(object):
	def __init__(self, user, params, url):
		self.user = user
		self.url = url
		# merge endpoint params with general params
		params.update(self.user.get_base_params())
		self.params = params
		self.data = self.__request()

	def __request(self):
		# check that the session token is valid
		user.session.is_token_valid()
		res = requests.get(self.url, headers=self.user.session.header, params=self.params)
		return res.json()

# for terminal output
class Console(object):
	@staticmethod
	def output_collection(iterable, keys):
		# take an iterable of dicts and get the key values to extract data from
		for item in iterable:
			print('{0}: {1: <51} | {2}: {3}'.format(keys[0], item[keys[0]], keys[1], item[keys[1]]))

class Browse(object):
	@staticmethod
	def featured_playlists(user):
		#endpoint specific values
		url = 'https://api.spotify.com/v1/browse/featured-playlists'
		params = {}

		res = ApiCall(user, params, url)
		Console().output_collection(res.data['playlists']['items'], ('name', 'uri'))

	@staticmethod
	def new_releases(user):
		url = 'https://api.spotify.com/v1/browse/new-releases'
		params = {}

		res = ApiCall(user, params, url)
		Console().output_collection(res.data['albums']['items'], ('name', 'uri'))

	@staticmethod
	def list_categories(user):
		url = 'https://api.spotify.com/v1/browse/categories'
		params = {'limit': 50}

		res = ApiCall(user, params, url)
		Console().output_collection(res.data['categories']['items'], ('name', 'id'))

	def list_playlists(user, id):
		url = 'https://api.spotify.com/v1/browse/categories/{0}/playlists'.format(id)
		params = {}

		res = ApiCall(user, params, url)
		Console().output_collection(res.data['playlists']['items'], ('name','uri'))

class Search(object):
	@staticmethod
	def find(user, query, search_type):
		# endpoint specific values
		url = 'https://api.spotify.com/v1/search'
		params = {'q': query, 'type': search_type, 'limit': 5}

		res = ApiCall(user, params, url)

		if search_type == 'artist':
			Console().output_collection(res.data[search_type + 's']['items'], ('name', 'id'))
		else:
			Console().output_collection(res.data[search_type + 's']['items'], ('name', 'uri'))

class Artist(object):
	@staticmethod
	def list_albums(user, id):
		# endpoint specific values
		url = 'https://api.spotify.com/v1/artists/{0}/albums'.format(id)
		params = {'album_type': 'album', 'market': 'US'}

		res = ApiCall(user, params, url)
		Console().output_collection(res.data['items'], ('name', 'id'))

	@staticmethod
	def list_related(user, id):
		url = 'https://api.spotify.com/v1/artists/{0}/related-artists'.format(id)
		params = {}
		
		res = ApiCall(user, params, url)
		Console().output_collection(res.data['artists'], ('name', 'id'))
			
# using the argparse library to simplify CLI set-up
parser = argparse.ArgumentParser(description='Access the Spotify API from the command line.')
subparsers = parser.add_subparsers(help='Learn more about the various API categories.', dest='category')

parser_artists = subparsers.add_parser('artists', help='Interact with the Artists resource.')
parser_artists.add_argument('--id', nargs='?', help='The Spotify artist ID.', required=True)
parser_artists.add_argument('--endpoint', nargs='?', help='Select the resource\'s endpoint.',
					choices=['related', 'albums'])

parser_search = subparsers.add_parser('search', help='Search for artists, albums, and tracks.')
parser_search.add_argument('--query', nargs='?', help='The search query.', required=True)
parser_search.add_argument('--type', nargs='?', help="The resource to search through.",
					choices=['album', 'artist', 'track'], required=True)

parser_browse = subparsers.add_parser('browse', help='Get playlists and album release info.')
parser_browse.add_argument('--endpoint', nargs='?', help='Select the resource\'s endpoint.',
					choices=['featured-playlists', 'new-releases', 'categories'])
parser_browse.add_argument('--id', nargs='?', help='The Spotify category ID.')



### begin execution ###

args = parser.parse_args()
user = User()

# artists subparser
if args.category == 'artists':
	if args.endpoint == 'related':
		Artist.list_related(user, args.id)
	else:
		Artist.list_albums(user, args.id)

# browse subparser
elif args.category == 'browse':
	if args.endpoint == 'featured-playlists':
		Browse.featured_playlists(user)
	elif args.endpoint == 'new-releases':
		Browse.new_releases(user)
	else:
		if args.id:
			Browse.list_playlists(user, args.id)
		else:
			Browse.list_categories(user)

# search subparser
else:
	Search.find(user, args.query, args.type)