import os
import socket
import uuid

from couchdb.client import Server
from couchdb.http import PreconditionFailed
from couchdb.design import ViewDefinition

from daybed import logger
from .views import docs

from . import views
from ..exceptions import (
    OAuthAccessTokenNotFound, StateNotFound,
    UserTokenNotFound, UserTokenAlreadyExist, RedirectURINotFound
)


class CouchDBBackendConnectionError(Exception):
    pass


class CouchDBBackend(object):

    @classmethod
    def load_from_config(cls, config):
        settings = config.registry.settings
        return CouchDBBackend(
            host=settings['backend.db_host'],
            db_name=os.environ.get('DB_NAME', settings['backend.db_name']),
        )

    def __init__(self, host, db_name, id_generator):
        self.server = Server(host)
        self.db_name = db_name

        try:
            self.create_db_if_not_exist()
        except socket.error as e:
            raise CouchDBBackendConnectionError(
                "Unable to connect to the CouchDB server: %s - %s" % (host, e))

        self._db = self.server[self.db_name]
        self.sync_views()

    def delete_db(self):
        del self.server[self.db_name]

    def create_db_if_not_exist(self):
        try:
            self.server.create(self.db_name)
            logger.info('Creating and using db "%s"' % self.db_name)
        except PreconditionFailed:
            logger.info('Using db "%s".' % self.db_name)

    def sync_views(self):
        ViewDefinition.sync_many(self.server[self.db_name], docs)

    def __get_raw_user_token(self, user_id):
        try:
            return views.usertokens(self._db, key=user_id).rows[0].value
        except IndexError:
            raise UserTokenNotFound(user_id)

    def get_user_token(self, user_id):
        """Returns the information associated with a user token"""
        usertoken = dict(**self.__get_raw_user_token(user_id))
        return usertoken['token']

    def add_token(self, user_id, token):
        # Check that the token doesn't already exist.
        try:
            self.__get_raw_user_token(user_id)
            raise UserTokenAlreadyExist(user_id)
        except UserTokenNotFound:
            pass

        doc = dict(token=token, user_id=user_id, type='usertoken')
        self._db.save(doc)

    def __get_raw_state(self, session_id):
        try:
            return views.states(self._db, key=session_id).rows[0].value
        except IndexError:
            raise StateNotFound(session_id)

    def get_state(self, session_id):
        """Retrives the session_id state."""
        state_doc = dict(**self.__get_raw_state(session_id))
        return state_doc['state']

    def set_state(self, session_id):
        """Set a session_id state."""
        try:
            doc = self.__get_raw_state(session_id)
        except StateNotFound:
            doc = {"type": "fxa_oauth_states", "session_id": session_id}

        doc['state'] = uuid.uuid4().hex
        self._db.save(doc)
        return doc['state']

    def get_or_set_state(self, session_id):
        """Retrieves or creates a state for the session_id"""
        try:
            return self.get_state(session_id)
        except StateNotFound:
            return self.set_state(session_id)

    def __get_raw_redirect_uri(self, state):
        try:
            return views.redirect_uris(self._db, key=state).rows[0].value
        except IndexError:
            raise RedirectURINotFound(session_id)

    def get_state(self, state):
        """Retrives the session_id state."""
        redirect_uri_doc = dict(**self.__get_raw_state(state))
        return redirect_uri_doc['redirect_uri']

    def set_state(self, state, redirect_uri):
        """Set a redirect_uri."""
        try:
            doc = self.__get_raw_state(state)
        except RedirectURINotFound:
            doc = {"type": "fxa_oauth_redirect_uri", "state": state}
        doc['redirect_uri'] = redirect_uri
        self._db.save(doc)

    def __get_raw_oauth_access_token(self, session_id):
        try:
            return views.access_tokens(self._db, key=session_id).rows[0].value
        except IndexError:
            raise OAuthAccessTokenNotFound(session_id)

    def get_oauth_access_token(self, session_id):
        """Retrives the session_id oauth_access_token."""
        token_doc = dict(**self.__get_raw_oauth_access_tokens(session_id))
        return token_doc['access_token']

    def set_oauth_access_token(self, session_id, access_token):
        """Set the session_id oauth_access_token."""
        try:
            doc = self.__get_raw_oauth_access_tokens(session_id)
        except OAuthAccessTokenNotFound:
            doc = {"type": "fxa_oauth_access_tokens", "session_id": session_id}

        doc['access_token'] = access_token
        self._db.save(doc)
