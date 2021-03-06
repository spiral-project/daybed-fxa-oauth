import uuid

from ..exceptions import (
    OAuthAccessTokenNotFound, StateNotFound,
    UserTokenNotFound, UserTokenAlreadyExist, RedirectURINotFound
)


class MemoryBackend(object):

    @classmethod
    def load_from_config(cls, config):
        return MemoryBackend()

    def __init__(self):
        self._init_db()

    def delete_db(self):
        self._db.clear()
        self._init_db()

    def _init_db(self):
        self._db = {
            'user_tokens': {},
            'redirect_uris': {},
            'session_states': {},
            'session_oauth_access_tokens': {}
        }

    def get_user_token(self, user_id):
        """Retrieves a token for the userid"""
        try:
            return str(self._db['user_tokens'][user_id])
        except KeyError:
            raise UserTokenNotFound(user_id)

    def store_user_token(self, user_id, token):
        # Check that the token doesn't already exist.
        try:
            self.get_user_token(user_id)
            raise UserTokenAlreadyExist(user_id)
        except UserTokenNotFound:
            pass

        self._db['user_tokens'][user_id] = token

    def get_redirect_uri(self, state):
        """Retrieves a redirect URI for the given state"""
        try:
            return str(self._db['redirect_uris'][state])
        except KeyError:
            raise RedirectURINotFound(user_id)

    def set_redirect_uri(self, state, redirect_uri):
        self._db['redirect_uris'][state] = token

    def get_state(self, session_id):
        """Retrives the session_id state."""
        if session_id in self._db['session_states']:
            return self._db['session_states'][session_id]
        else:
            raise StateNotFound(session_id)

    def set_state(self, session_id):
        """Set a session_id state."""
        state = uuid.uuid4().hex
        self._db['session_states'][session_id] = state
        return state

    def get_or_set_state(self, session_id):
        """Retrieves or creates a state for the session_id"""
        try:
            return self.get_state(session_id)
        except StateNotFound:
            return self.set_state(session_id)

    def get_oauth_access_token(self, session_id):
        """Retrives the session_id oauth_access_token."""
        if session_id in self._db['session_oauth_access_tokens']:
            return self._db['session_oauth_access_tokens'][session_id]
        else:
            raise OAuthAccessTokenNotFound(session_id)

    def set_oauth_access_token(self, session_id, access_token):
        """Set the session_id oauth_access_token."""
        self._db['session_oauth_access_tokens'][session_id] = access_token
