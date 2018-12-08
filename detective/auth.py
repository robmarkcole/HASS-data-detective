"""Auth helper."""
import json
import os

from . import config


def auth_from_hass_config(path=None, **kwargs):
    """Initialize auth from HASS config."""
    if path is None:
        path = config.find_hass_config()

    return Auth(os.path.join(path, '.storage/auth'), **kwargs)


class Auth:
    """Class to hold auth."""

    def __init__(self, auth_path):
        """Load auth data and store in class."""
        with open(auth_path) as fp:
            auth = json.load(fp)

        self.users = {user['id']: user for user in auth['data']['users']}
        self.refresh_tokens = {
            token['id']: {
                'id': token['id'],
                'user': self.users[token['user_id']],
                'client_name': token['client_name'],
                'client_id': token['client_id'],
            } for token in auth['data']['refresh_tokens']
        }

    def user_name(self, user_id):
        """Return name for user."""
        user = self.users.get(user_id)

        if user is None:
            return "Unknown user ({})".format(user_id)

        return user['name']
