import pkg_resources
from pyramid.config import ConfigurationError
from pyramid.settings import aslist

#: Module version, as defined in PEP-0396.
__version__ = pkg_resources.get_distribution(__package__).version


def includeme(config):
    settings = config.get_settings()
    if 'fxa-oauth.client_id' not in settings:
        raise ConfigurationError(
            'Missing fxa-oauth.client_id setting. This is needed to enable FxA OAuth'
        )

    if 'fxa-oauth.client_secret' not in settings:
        raise ConfigurationError(
            'Missing fxa-oauth.client_secret setting. This is needed to enable FxA OAuth'
        )

    oauth_uri = settings.get("fxa-oauth.oauth_uri", "https:/oauth.accounts.firefox.com/v1")
    content_uri = settings.get("fxa-oauth.content_uri", "https://accounts.firefox.com")
    profile_uri = settings.get("fxa-oauth.profile_uri", "https://profile.firefox.com/v1")
    redirect_uri = settings.get("fxa-oauth.redirect_uri",
                                "urn:ietf:wg:oauth:2.0:fx:webchannel")
    scope = settings.get("fxa-oauth.scope", "profile")

    config.registry['fxa-oauth.oauth_uri'] = oauth_uri
    config.registry['fxa-oauth.content_uri'] = content_uri
    config.registry['fxa-oauth.profile_uri'] = profile_uri
    config.registry['fxa-oauth.redirect_uri'] = redirect_uri
    config.registry['fxa-oauth.scope'] = scope

    # Create a backend and use the daybed_fxa_oauth prefix for it.
    backend_class = config.maybe_dotted(
        settings.get('fxa-oauth.backend',
                     settings['daybed.backend'].replace('daybed',
                                                        'daybed_fxa_oauth'))
    )
    config.registry.fxa_oauth_db = backend_class.load_from_config(config)

    config.scan("daybed_fxa.views")
