import httplib, urllib, ConfigParser, logging, json
from functools import reduce


# setup the logger
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# get the login details from the configuration file
config = ConfigParser.RawConfigParser()
config.read('configuration')

try :
    ig_username = config.get("ig","username")
    ig_password = config.get("ig","password")
    ig_api_key = config.get("ig","api_key")
    splunk_http_server = config.get("splunk","host")
    splunk_collection_url = config.get("splunk","collection_url")
    splunk_token = config.get("splunk", "token")

except ConfigParser.NoSectionError:
    logger.error("cannot open login details")
    exit(1)
except ConfigParser.NoOptionError:
    logger.error("cannot open login details missing")
    exit(1)

# create a headers for logging into ig index
ig_headers = {
'Content-Type': 'application/json; charset=UTF-8',
'Accept': 'application/json; charset=UTF-8',
'VERSION': '2',
'X-IG-API-KEY': ig_api_key
}

# create the body for logging in
ig_body = '{"identifier":"' + ig_username + '", "password":"' + ig_password + '", "encryptedPassword":"null"}'

splunk_headers={
'Authorization': 'Splunk ' + splunk_token
}

# get the connection to IG index and login
ig_connection = httplib.HTTPSConnection("api.ig.com")
ig_connection.request("POST", "/gateway/deal/session", body=ig_body, headers=ig_headers)
session_response = ig_connection.getresponse()

# get the session keys for further queries
token = session_response.getheader("x-security-token")
cst = session_response.getheader("cst")
session_response_str = session_response.read(10000000)
logger.debug(session_response_str)
json_response = json.loads(session_response_str)

splunk_headers={
'Authorization': 'Splunk ' + splunk_token
}

splunk_body = '{"sourcetype": "ig-account", "event":' + session_response_str +'}'
splunk_connection = httplib.HTTPSConnection(splunk_http_server)
splunk_connection.request("POST", splunk_collection_url, body=splunk_body, headers=splunk_headers)
splunk_response = splunk_connection.getresponse()
splunk_response_json = json.load(splunk_response)

# if we didn't login exit and report a failure
if "errorCode" in json_response:
    logger.error("login failed")
    exit(-1)

# create the header for further queries
position_headers = {
'Content-Type': 'application/json; charset=UTF-8',
'Accept': 'application/json; charset=UTF-8',
'VERSION': '2',
'X-IG-API-KEY': ig_api_key,
'x-security-token': token,
'cst': cst
}

# get our current positions
ig_connection.request("GET", "/gateway/deal/positions", headers=position_headers)

position_response_str = ig_connection.getresponse().read(10000000)
logger.debug(position_response_str)
position_response_json = json.loads(position_response_str)

for position in position_response_json["positions"]:
    # create the body for logging in
    position = json.dumps(position)
    print position
    splunk_positions_body = '{"sourcetype": "ig-position", "event":' + json.dumps(position) + '}'
    splunk_connection.request("POST", splunk_collection_url, body=splunk_positions_body, headers=splunk_headers)
    print splunk_connection.getresponse()










