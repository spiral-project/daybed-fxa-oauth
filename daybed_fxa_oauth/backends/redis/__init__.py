# -*- coding: utf-8 -*-
import redis
import uuid

from ..exceptions import (
    OAuthAccessTokenNotFound, StateNotFound,
    UserIdNotFound, UserIdAlreadyExist, RedirectURINotFound
)


class RedisBackend(object):

    @classmethod
    def load_from_config(cls, config):
        settings = config.registry.settings

        return RedisBackend(
            settings.get('backend.db_host', 'localhost'),
            settings.get('backend.db_port', 6379),
            settings.get('backend.db_index', 0)
        )

    def __init__(self, host, port, db):
        self._db = redis.StrictRedis(host=host, port=port, db=db)

        # Ping the server to be sure the connection works.
        self._db.ping()

    def delete_db(self):
        self._db.flushdb()

    def get_user_token(self, user_id):
        """Retrieves a token for the userid"""
        token = self._db.get("usertoken.%s" % user_id)
        if token is None:
            raise UserIdNotFound(user_id)
        return token.decode("utf-8")

    def store_user_token(self, user_id, token):
        # Check that the token doesn't already exist.
        try:
            self.get_user_token(user_id)
            raise UserIdAlreadyExist(user_id)
        except UserIdNotFound:
            pass

        self._db.set("usertoken.%s" % user_id, token)

    def get_redirect_uri(self, state):
        """Retrives the redirect_uri for the state."""
        redirect_uri = self._db.get("fxa_oauth_redirect_uri.%s" % state)
        if redirect_uri is None:
            raise RedirectURINotFound(session_id)
        return redirect_uri.decode("utf-8")

    def set_redirect_uri(self, state, redirect_uri):
        """Set a session_id state."""
        self._db.set("fxa_oauth_redirect_uri.%s" % state, redirect_uri)

    def get_state(self, session_id):
        """Retrives the session_id state."""
        state = self._db.get("fxa_oauth_states.%s" % session_id)
        if state is None:
            raise StateNotFound(session_id)
        return state.decode("utf-8")

    def set_state(self, session_id):
        """Set a session_id state."""
        state = uuid.uuid4().hex
        self._db.set("fxa_oauth_states.%s" % session_id, state)
        return state

    def get_or_set_state(self, session_id):
        """Retrieves or creates a state for the session_id"""
        try:
            return self.get_state(session_id)
        except StateNotFound:
            return self.set_state(session_id)

    def get_oauth_access_token(self, session_id):
        """Retrives the session_id oauth_access_token."""
        access_token = self._db.get("fxa_oauth_access_token.%s" % session_id)
        if access_token is None:
            raise OAuthAccessTokenNotFound(session_id)
        return access_token.decode("utf-8")

    def set_oauth_access_token(self, session_id, access_token):
        """Set the session_id oauth_access_token."""
        self._db.set("fxa_oauth_access_token.%s" % session_id, access_token)
