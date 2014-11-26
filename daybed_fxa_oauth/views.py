# -*- coding: utf-8 -*-
import json
import logging
import re
import requests
import uuid

from urllib import urlencode

from pyramid.httpexceptions import HTTPFound
from daybed.tokens import get_hawk_credentials, hmac_digest
from cornice import Service
from colander import MappingSchema, SchemaNode, String, Regex

from .backends.exceptions import (
    OAuthAccessTokenNotFound, StateNotFound, UserIdNotFound, RedirectURINotFound
)

logger = logging.getLogger(__name__)


params = Service(name='fxa-oauth params', path='/tokens/fxa-oauth/params')
token = Service(name='fxa-oauth-token', path='/tokens/fxa-oauth/token')
redirect = Service(name='fxa-oauth-redirect', path='/tokens/fxa-oauth/redirect')

# This one comes from Django
# https://github.com/django/django/blob/273b96/
# django/core/validators.py#L45-L52
URLPATTERN = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def validate_session_cookie(request):
    if 'session_id' not in request.cookies:
        request.errors.add('body', 'session cookie',
                           'session cookie not defined')
        request.errors.status = 401


class ParamsRequest(MappingSchema):
    redirect_uri = SchemaNode(
        String(), validator=Regex(URLPATTERN, msg="Invalid URL"),
        location="body")


@params.post(schema=ParamsRequest)
def get_fxa_parameters(request):
    """Provide the client with the parameters needed for the OAuth dance."""
    db = request.registry.fxa_oauth_db

    # If no cookie had been sent, create one
    if 'session_id' not in request.cookies:
        session_id = uuid.uuid4().hex
        request.response.set_cookie('session_id', session_id)
    else:
        session_id = request.cookies['session_id']

    # Create a session and attach a state to it.
    state = db.get_or_set_state(session_id)
    db.set_redirect_uri(state, request.validated['redirect_uri'])

    return {
        "client_id": request.registry['fxa-oauth.client_id'],
        "redirect_uri": request.registry['fxa-oauth.redirect_uri'],
        "profile_uri": request.registry['fxa-oauth.profile_uri'],
        "content_uri": request.registry['fxa-oauth.content_uri'],
        "oauth_uri": request.registry['fxa-oauth.oauth_uri'],
        "scope": request.registry['fxa-oauth.scope'],
        "state": state
    }


class OAuthRequest(MappingSchema):
    code = SchemaNode(String(), location="body")
    state = SchemaNode(String(), location="body")


@token.post(validators=[validate_session_cookie], schema=OAuthRequest)
def trade_token(request):
    """Trade an OAuth code with an oauth bearer token."""
    db = request.registry.fxa_oauth_db
    session_id = request.cookies['session_id']

    code = request.validated['code']
    state = request.validated['state']

    try:
        stored_state = db.get_state(session_id)
    except StateNotFound:
        request.errors.add('body', 'session cookie',
                           'session cookie not found')
        request.errors.status = 404
        return

    redirect_uri = db.get_redirect_uri(state)

    db.set_state(session_id)
    if stored_state != state:
        request.errors.add('body', 'state', 'invalid oauth state')
        return

    resp = requests.post(
        '%s/token' % request.registry['fxa-oauth.oauth_uri'],
        data=json.dumps({
            "code": code,
            "client_id": request.registry['fxa-oauth.client_id'],
            "client_secret": request.registry['fxa-oauth.client_secret']
        }),
        headers={'Content-Type': 'application/json'}
    )

    if not 200 <= resp.status_code < 300:
        print "oops, fxa server isn't working"
        request.response.status = 503
        return

    oauth_server_response = resp.json()
    token = oauth_server_response['access_token']

    db.set_oauth_access_token(session_id, token)

    resp = requests.get(
        '%s/profile' % request.registry['fxa-oauth.profile_uri'],
        headers={
            'Authorization': 'Bearer %s' % token,
            'Accept': 'application/json'
        }
    )

    if not 200 <= resp.status_code < 300:
        print "oops, profile server isn't working"
        request.response.status = 503
        return

    data = resp.json()
    email = data['email']
    uid = data['uid']

    uid_hmaced = hmac_digest(request.registry.tokenHmacKey,
                             "%s:%s" % (redirect_uri, uid))
    is_new = False
    try:
        token = db.get_user_token(uid_hmaced)
    except UserIdNotFound:
        is_new = True
        token = None

    token, credentials = get_hawk_credentials(token)

    if is_new:
        db.store_user_token(uid_hmaced, token)
        request.db.store_credentials(token, credentials)
        request.response.status = 201

    return {
        'token': token,
        'credentials': credentials,
        'profile': {
            'uid': uid,
            'email': email
        }
    }


@redirect.get()
def redirect_to_app(request):
    db = request.registry.fxa_oauth_db
    try:
        redirect_uri = db.get_redirect_uri(request.params.get('state'))
    except RedirectUrlNotFound:
        request.response.status = 400
        return

    url = "%s?%s" % (redirect_uri, urlencode(request.params))

    return HTTPFound(location=url)
