import logging
import ConfigParser
import sys, tweepy, json
from unidecode import unidecode
sys.path.append('./database/DAO')
from DatabaseManager import DatabaseManager
from Tweet import Tweet
from User import User

logging.basicConfig(format='%(asctime)s %(message)s', filename='debug.log', level=logging.ERROR)

class CustomStreamListener(tweepy.StreamListener):

	def setDBM(self, dbm):
		self.dbm = dbm

	def on_data(self, data):
		"""Recieve raw data from stream"""


		logging.debug("CustomStreamListener: on_data")
		obj = json.loads(data.decode("latin-1"))

		# Find the user...
		logging.debug("CustomStreamListener: Finding user")
		try:
			user = User.searchUserById(self.dbm, obj['user']['id'])

			logging.debug("CustomStreamListener: User ID = {}".format(user.idUser))

			if user.idUser == 0:

				logging.debug("CustomStreamListener: User not found")
				logging.debug("CustomStreamListener: Creating user")

				user.set(obj['user']['id'],
						 created_at = obj['user']['created_at'], #description = obj['user']['description'],
						 followers_count = obj['user']['followers_count'],
						 friends_count = obj['user']['friends_count'], 
						 geo_enabled = obj['user']['geo_enabled'], 
						 location = unidecode(obj['user']['location']), 
						 name = unidecode(obj['user']['name']), 
						 protected = obj['user']['protected'], 
						 time_zone = obj['user']['time_zone'], 
						 url = obj['user']['url'],
						 verified = obj['user']['verified'])
				user.saveOrUpdate()
		except:
			# This means that user was null
			logging.debug("CustomStreamListener: User was null")

		# Create the tweet and save it
		logging.debug("CustomStreamListener: Saving tweet")
		try:
			logging.debug("\t... Creating tweet")
			tweet = Tweet(self.dbm)

			logging.debug("\t... Setting attributes")
			tweet.set(tweet_id_str = obj['id_str'],
					  from_user = obj['user']['id'],
					  tweet = unidecode(obj['text']),
					  created_at = obj['created_at'],
					  favorite_count = obj['favorite_count'],
					  retweet_count = obj['retweet_count'],
					  coordinates = obj['coordinates'],
					  lang = obj['lang'],
				  	  filter_level = obj['filter_level'],
				  	  in_reply_to_status_id_str = obj['in_reply_to_status_id_str'])

			logging.debug("\t... Saving")
			tweet.save()

			logging.debug("CustomStreamListener: Tweet saved with id = {}".format(obj['id_str']))
			print "Saving: u_id = {} | id_str = {}".format(obj['user']['id'], obj['id_str'])
		except Exception, e:
			logging.error("CustomStreamListener: Error in tweet {}".format(obj["id_str"]))
			logging.error("CustomStreamListener: {}".format(e))
			print "ERR: {}".format(obj['id_str'])

	def on_error(self, status_code):
		print >> sys.stderr, 'Encountered status error with code: ', status_code
		return True #Don't kill the stream

	def on_timeout(self):
		print >> sys.stderr, 'Timeout...'
		return True #Don't kill the stream

class Listener(tweepy.StreamListener):
    def on_status(self, status):
        print "screen_name='%s' tweet='%s'"%(status.author.screen_name, status.text)

def main():
	logging.info("Reading config file")
	config = ConfigParser.ConfigParser()
	config.read("config.ini")

	logging.info("Creating dbm")
	dbm = DatabaseManager(host = config.get("MySQLDB", "host"),
						  user = config.get("MySQLDB", "user"),
						  passwd = config.get("MySQLDB", "passwd"),
						  db = config.get("MySQLDB", "db"))


	logging.info("Creating tweepy object")
	logging.info("Tweepy: OAuthHandler")
	auth = tweepy.OAuthHandler( config.get("TwitterAPI", "consumer_key"),
								config.get("TwitterAPI", "consumer_secret"))
	logging.info("Tweepy: Access Token")
	auth.set_access_token(config.get("TwitterAPI", "access_token"),
						  config.get("TwitterAPI", "access_token_secret"))

	logging.info("Tweepy: Authenticating")
	api = tweepy.API(auth)
	logging.info("Tweepy: Creating streaming object")
	csl = CustomStreamListener()
	csl.setDBM(dbm)
	sapi = tweepy.streaming.Stream(auth, csl)
	# sapi = tweepy.streaming.Stream(auth, Listener())
	# ITAM locations=[19.344981, -99.199943]

	# Mexico City
	# North Bound (19.586154, -99.123314)
	# South Bound (19.084182, -99.067948)
	#sapi.filter(languages=['es'], locations=[-99.2, 19.1, -99, 19.5])

	#Mexico City and Mexico State                                                                                   
	sapi.filter(locations=[-100.61,18.36,-97.76,20.91])

	# San Diego
	# sapi.filter(locations=[-117.28,32.65,-116.91,32.88], async=False) 

	# Tijuana
	# sapi.filter(locations=[-117.12,32.45,-116.84,32.55], async=False)

	# SD o Tijuana
	#sapi.filter(locations=[-117.28,32.65,-116.91,32.88,-117.12,32.45,-116.84,32.55], async=False) 




if __name__ == '__main__':
	main()