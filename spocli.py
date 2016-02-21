# general libraries
import requests, os, base64, time, datetime, sys, argparse

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

# a class for API calls
class ApiCall(object):
	def __init__(self, params, url):
		self.res = self.__get(params, url)

	def __get(self, params, url):
		# merge endpoint params with general params
		user = User()
		params.update(user.get_base_params())
		user.session.is_token_valid()
		res = requests.get(url, headers=user.session.header, params=params)
		return res.json()

	def output_collection(self, keys):
		# extract the iterable object from the response
		iterable_keys = keys[0]

		# specify which values to extract from the iterable items
		value_keys = keys[1]

		iterable = self.res

		for key in iterable_keys:
			iterable = iterable[key]

		# take an iterable of dicts and get the key values to extract data from
		for item in iterable:
			print('{0}: {1: <51} | {2}: {3}'.format(value_keys[0], item[value_keys[0]], 
													value_keys[1], item[value_keys[1]]))



# below are API endpints mapped to functions

def find(query, search_type):
	# endpoint specific values
	url = 'https://api.spotify.com/v1/search'
	params = {'q': query, 'type': search_type, 'limit': 5}
	output_id = ((search_type + 's', 'items'), ('name', 'id'))
	output_uri = ((search_type + 's', 'items'), ('name', 'uri'))

	res = ApiCall(params, url)

	if search_type == 'artist':
		res.output_collection(output_id)
	else:
		res.output_collection(output_uri)

def browse_featured_playlists():
	url = 'https://api.spotify.com/v1/browse/featured-playlists'
	params = {}
	output = (('playlists', 'items'), ('name', 'uri'))

	res = ApiCall(params, url)
	res.output_collection(output)

def browse_new_releases():
	url = 'https://api.spotify.com/v1/browse/new-releases'
	params = {}
	output = (('albums', 'items'), ('name', 'uri'))

	res = ApiCall(params, url)
	res.output_collection(output)

def browse_list_categories():
	url = 'https://api.spotify.com/v1/browse/categories'
	params = {'limit': 50}
	output = (('categories', 'items'), ('name', 'id'))

	res = ApiCall(params, url)
	res.output_collection(output)

def browse_list_playlists(id):
	url = 'https://api.spotify.com/v1/browse/categories/{0}/playlists'.format(id)
	params = {}
	output = (('playlists', 'items'), ('name','uri'))

	res = ApiCall(params, url)
	res.output_collection(output)

def artists_list_albums(id):
	# endpoint specific values
	url = 'https://api.spotify.com/v1/artists/{0}/albums'.format(id)
	params = {'album_type': 'album', 'market': 'US'}
	output = (('items', ), ('name', 'id'))

	res = ApiCall(params, url)
	res.output_collection(output)


def artists_list_related(id):
	url = 'https://api.spotify.com/v1/artists/{0}/related-artists'.format(id)
	params = {}
	output = (('artists', ), ('name', 'id'))
	
	res = ApiCall(params, url)
	res.output_collection(output)

def build_parser():
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

	return parser

def main():
	parser = build_parser()
	args = parser.parse_args()

	# artists subparser
	if args.category == 'artists':
		if args.endpoint == 'related':
			artists_list_related(args.id)
		else:
			artists_list_albums(args.id)

	# browse subparser
	elif args.category == 'browse':
		if args.endpoint == 'featured-playlists':
			browse_featured_playlists()
		elif args.endpoint == 'new-releases':
			browse_new_releases()
		else:
			if args.id:
				browse_list_playlists(args.id)
			else:
				browse_list_categories()

	# search subparser
	elif args.category == 'search':
		find(args.query, args.type)

	# show help
	else:
		parser.print_help()

if __name__ == '__main__':
	sys.exit(main())