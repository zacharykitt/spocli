import requests, os, base64, time, datetime, sys, argparse, dbus

# The User class may be overkill for the current version of this script,
# but it could be useful in a more robust program to have a persistent
# user object.

class User(object):
	def __init__(self):
		self.locale = "en_US"
		self.country = "US"
		self.session = Session()

	def get_local_time(self):
			return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

	def get_base_params(self):
		return {'country': self.country, 'locale': self.locale, 'timestamp': self.get_local_time()}



# The Session class allows for tokens to be created and saved to the current
# user. Header information for each request is also stored within the session
# object.

class Session(object):
	# constant values for token endpoint
	url = "https://accounts.spotify.com/api/token"
	data = {'grant_type': 'client_credentials'}

	def __init__(self):
		self.encoded_credentials = self.__encode_credentials(os.environ['SPOTIFY_CREDS'])
		self.token_dict = self.__get_auth_token()
		self.header = self.__set_header()

	# API keys need to be encoded in base64
	def __encode_credentials(self, credentials):
		credentials = bytes(credentials, encoding='utf-8')
		return base64.b64encode(credentials)

	def __get_auth_token(self):
		# pass credentials in request header
		headers = {'Authorization': 'Basic %s' % self.encoded_credentials.decode('utf-8')}

		# make request to proper endpoint 
		res = requests.post(self.url, headers=headers, data=self.data)
		
		token_dict = res.json()

		# add a created_at value for checking expiratio(
		token_dict['created_at'] = int(time.time())

		return token_dict


	# set the session header used for requests
	def __set_header(self):
		auth_string = '{0} {1}'.format(self.token_dict['token_type'], self.token_dict['access_token'])
		return {'Authorization': auth_string}	


	# tokens expire after 3600s
	def is_token_valid(self):
		# get current time and leave room for error
		current = int(time.time())
		token_expiration = self.token_dict['created_at'] + 3500 # NOT a typo
		if current >= token_expiration:
			self.__get_auth_token()
			self.__set_header()



# Create a dbus connection to the desktop Spotify application. Therefore this
# feature will only work on linux desktops for the timebeing.

class Player(object):
	def __init__(self):
		session_bus = dbus.SessionBus()
		connection_name = 'org.mpris.MediaPlayer2.spotify'
		connection_path = '/org/mpris/MediaPlayer2'
		self.app_interface_name = 'org.mpris.MediaPlayer2'
		self.player_interface_name = 'org.mpris.MediaPlayer2.Player'
		self.props_interface_name = 'org.freedesktop.DBus.Properties'
		
		proxy = session_bus.get_object(connection_name, connection_path)

		self.player_interface = dbus.Interface(proxy, self.player_interface_name)
		self.props_interface = dbus.Interface(proxy, self.props_interface_name)
		self.app_interface = dbus.Interface(proxy, self.app_interface_name)
		# note to self: see proxy commands with print(proxy.Introspect())

	def playpause(self):
		self.player_interface.PlayPause()

	def stop(self):
		self.player_interface.Stop()

	def next(self):
		self.player_interface.Next()

	def previous(self):
		# only resets track position
		self.player_interface.Stop()
		self.player_interface.Previous()
		self.player_interface.PlayPause()

	def open(self, uri):
		self.player_interface.OpenUri(uri)

	def info(self):
		metadata = self.props_interface.Get(self.player_interface_name, 'Metadata')
		print('Track: {0}\nAlbum: {1}\nArtist: {2}'.format(metadata['xesam:title'], 
								metadata['xesam:album'], metadata['xesam:artist'][0]))

# Cut down on some repititon by abstracting parts of the API call and response.
# Currently each API call creates a new user object since the program terminates
# upon completion of a request. A persistent version of this program would
# require that the user object be passed to it.

class ApiCall(object):
	def __init__(self, params, url, user = None):
		if user is None:
			user = User()
		self.user = user
		self.res = self.__get(params, url)

	def __get(self, params, url):
		# merge endpoint params with general params
		params.update(self.user.get_base_params())

		# the following would only be necessary for a persistent version of 
		# this program:
		# self.user.session.is_token_valid()

		res = requests.get(url, headers=self.user.session.header, params=params)
		return res.json()

	def __extract_iterable_object(self, keys):
		iterable = self.res

		for k in keys:
			iterable = iterable[k]

		return iterable

	def output_collection(self, keys):
		# extract the iterable object from the response
		iterable = self.__extract_iterable_object(keys[0])

		# specifies which values to extract from the iterable items
		values = keys[1]

		# take an iterable of dicts and get the key values to extract data from
		for i in iterable:
			print('{0}: {1: <51} | {2}: {3}'.format(values[0], i[values[0]], values[1], i[values[1]]))



# The following are functions that map to API endpoints. The endpoint structure 
# is pretty repetitious but not constant, which has stopped be from being able 
# to come up with a quick solution for abstracting endpoints. Functions seem 
# like an okay choice since they mirror HTTP requests (verbs).

def find(query, search_type):
	# endpoint specific values
	url = 'https://api.spotify.com/v1/search'
	params = {'q': query, 'type': search_type}
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
	output = (('items', ), ('name', 'uri'))

	res = ApiCall(params, url)
	res.output_collection(output)


def artists_list_related(id):
	url = 'https://api.spotify.com/v1/artists/{0}/related-artists'.format(id)
	params = {}
	output = (('artists', ), ('name', 'id'))
	
	res = ApiCall(params, url)
	res.output_collection(output)



# This function builds the parser (using the argparse library). Each API 
# category has been turned into its own subparser to allow for a semblance of 
# organization.

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

	parser_player = subparsers.add_parser('player', help='Control the desktop Spotify application.')
	parser_player.add_argument('--command', nargs='?', help='Enter the player command.',
						choices=['play', 'pause', 'stop', 'next', 'previous', 'open', 'info'])
	parser_player.add_argument('--uri', nargs='?', help='The Spotify resource\'s URI.')

	return parser



# Read the system arguments and perform the associated function. This could
# maybe be refactored so that the API categories are objects and a constructor
# calls the correct endpoint function based off the params passed to it. For
# now nested conditional statements are acceptable (complexity is low).

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

	elif args.category == 'player':
		player = Player()

		if args.command == 'play' or args.command == 'pause':
			player.playpause()
		elif args.command == 'stop':
			player.stop()
		elif args.command == 'next':
			player.next()
		elif args.command == 'previous':
			player.previous()
		elif args.command == 'open':
			player.open(args.uri)
		elif args.command == 'info':
			player.info()
		else:
			pass

	# show help
	else:
		parser.print_help()

if __name__ == '__main__':
	sys.exit(main())