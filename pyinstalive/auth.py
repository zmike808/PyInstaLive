import codecs
import datetime
import json
import os.path
import sys
import re
import traceback

try:
    import logger
    import helpers
    import pil
except ImportError:
    from . import logger
    from . import helpers
    from . import pil

try:
    from instagram_private_api import (
        Client, ClientError, ClientCheckpointRequiredError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError)
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientCheckpointRequiredError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object.get('__class__') == 'bytes':
        return codecs.decode(json_object.get('__value__').encode(), 'base64')
    return json_object


def onlogin_callback(api, cookie_file):
    cache_settings = api.settings
    with open(cookie_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        logger.info('New cookie file was made: {0!s}'.format(os.path.basename(cookie_file)))
        logger.separator()


def authenticate(username, password, force_use_login_args=False):
    ig_api = None
    try:
        if force_use_login_args:
            pil.ig_user = username
            pil.ig_pass = password
            pil.config_login_overridden = True
            logger.binfo("Overriding configuration file login with -u and -p arguments.")
            logger.separator()
        cookie_file = os.path.join(os.path.dirname(pil.config_path), "{}.json".format(username))
        if not os.path.isfile(cookie_file):
            # settings file does not exist
            logger.warn('Unable to find cookie file: {0!s}'.format(os.path.basename(cookie_file)))
            logger.info('Creating a new one.')

            # login new
            # ig_api = Client(
            #     username, password,
            #     on_login=lambda x: onlogin_callback(x, cookie_file), proxy=pil.proxy)
            api = Client(username, password, on_login=lambda x: onlogin_callback(x, cookie_file), proxy=pil.proxy)
            try:
                api.login()
            except ClientCheckpointRequiredError as e:
                challenge_url = e.challenge_url

                challenge_pattern = r'.*challenge/(?P<account_id>\d.*)/(?P<identifier>\w.*)/'
                match = re.search(challenge_pattern, challenge_url)
                if not match:
                    raise ClientError('Unable to parse challenge')

                match_dict = match.groupdict()
                account_id = match_dict['account_id']
                identifier = match_dict['identifier']

                res = api.choose_confirm_method(account_id,
                                                identifier)  # confirm_method param has default value 1, you can pass 0
                code = input('Enter code from email: ')
                api.send_challenge(account_id, identifier, code)
        else:
            with open(cookie_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            # logger.info('Using settings file: {0!s}'.format(cookie_file))

            device_id = cached_settings.get('device_id')
            # reuse auth cached_settings
            try:
                ig_api = Client(
                    username, password,
                    settings=cached_settings, proxy=pil.proxy)
                ig_api.login()

            except ClientCookieExpiredError as e:
                logger.warn('The current cookie file has expired, creating a new one.')

                ig_api = Client(
                    username, password,
                    device_id=device_id,
                    on_login=lambda x: onlogin_callback(x, cookie_file), proxy=pil.proxy)

    except (ClientLoginError, ClientError) as e:
        logger.separator()
        logger.error('Could not login: {:s}'.format(e.error_response))
        # logger.error('{:s}'.format(json.loads(e.error_response).get("message", e.error_response)))
        # logger.error('{:s}'.format(e.error_response))
        logger.separator()
    except Exception as e:
        if str(e).startswith("unsupported pickle protocol"):
            logger.warn("This cookie file is not compatible with Python {}.".format(sys.version.split(' ')[0][0]))
            logger.warn("Please delete your cookie file '{}.json' and try again.".format(username))
        else:
            logger.separator()
            logger.error('Unexpected exception: {:s}'.format(e))
        logger.separator()
    except KeyboardInterrupt:
        logger.separator()
        logger.warn("The user authentication has been aborted.")
        logger.separator()

    if ig_api:
        logger.info('Successfully logged into account: {:s}'.format(str(ig_api.authenticated_user_name)))
        if pil.show_cookie_expiry and not force_use_login_args:
            try:
                cookie_expiry = ig_api.cookie_jar.auth_expires
                logger.info('Cookie file expiry date: {:s}'.format(
                    datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%d at %I:%M:%S %p')))
            except Exception as e:
                logger.warn('An error occurred while getting the cookie file expiry date: {:s}'.format(str(e)))

        logger.separator()
        return ig_api
    else:
        return None
