# -*- coding: utf-8 -*-
import json
import logging
import requests

from cornice import Service
from daybed.tokens import get_hawk_credentials
from daybed.views.errors import forbidden_view
from daybed_browserid.backends.exceptions import UserIdNotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import SignedCookieSessionFactory

logger = logging.getLogger(__name__)


params = Service(name='fxa-oauth params', path='/tokens/fxa-oauth/params')
token = Service(name='fxa-oauth-token', path='/tokens/fxa-oauth/token')

def validate_session_cookie(request):
    if 'session_id' not in request.cookies:
        request.errors.add('body', 'session cookie',
                           'session cookie not defined')
        request.errors.status = 401


@params.post()
def get_fxa_parameters(request):
    """Provide the client with the parameters needed for the OAuth dance."""
    db = request.registry.fxa_oauth_db

    # If no cookie had been sent, create one
    if 'session_id' not in request.cookies:
        session_id = uuid.uuid4()
        request.response.set_cookie('session_id', session_id)
    else:
        session_id = request.cookies['session_id']

    # Create a session and attach a state to it.
    state = db.get_or_set_state(session_id)

    return {
        client_id: request.registry['fxa-oauth.client_id'],
        redirect_uri: request.registry['fxa-oauth.redirect_uri'],
        profile_uri: request.registry['fxa-oauth.profile_uri'],
        content_uri: request.registry['fxa-oauth.content_uri'],
        oauth_uri: request.registry['fxa-oauth.oauth_uri'],
        scope: request.registry['fxa-oauth.scope'],
        state: state
    }

@token.get(validators=[validate_session_cookie])
def get_access_token(request):
    db = request.registry.fxa_oauth_db
    try:
        access_token = db.get_oauth_access_token(request.cookies['session_id'])
    except KeyError:
        access_token = None
    return {
        access_token: access_token
    }

class OAuthRequest(SchemaNode):
    code = SchemaNode(String(), location="body", type="str")
    state = SchemaNode(String(), location="body" type="str")

@token.post(validators=[validate_session_cookie], schema=OAuthRequest)
def trade_token(request):
    """Trade an OAuth code with an oauth bearer token."""
    db = request.registry.fxa_oauth_db
    session_id = request.cookies['session_id']
    from pdb import set_trace; set_trace()

    code = request.validated['code']
    state = request.validated['state']

    stored_state = db.get_state(session_id)
    db.set_state(session_id)
    if stored_state != state:
        request.errors.add('body', 'state', 'invalid oauth state')
        return

    resp = requests.post(
        '%s/token' % request.registry['fxa-oauth.oauth_uri'],
        data=json.dumps({
            code: code,
            client_id: request.registry['fxa-oauth.client_id'],
            client_secret: request.registry['fxa-oauth.client_secret']
        }),
        headers={'Content-Type': 'application/json'}
    )

    if not 200 < resp.status_code < 300:
        print "oops, fxa server isn't working"
        request.response.status = 503
        return

    oauth_server_response = resp.json()
    token = oauth_server_response['access_token']
    tokenType = oauth_server_response['token_type']
    scope = oauth_server_response['scope']

    db.set_oauth_access_token(session_id, token)

    resp = requests.get('%s/profile' % request.registry['fxa-oauth.profile_uri'],
        headers={
            'Authorization': 'Bearer %s' % token,
            'Accept': 'application/json'
        }
    )

     if not 200 < resp.status_code < 300:
        print "oops, profile server isn't working"
        request.response.status = 503
        return

    data = resp.json()

    # see what we have in there.
    # create the hawk session (derived from the email)
    # store the email address.
