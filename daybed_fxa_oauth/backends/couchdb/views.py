from couchdb.design import ViewDefinition

"""The token from their ids"""
tokens = ViewDefinition('usertokens', 'by_user_id', """
function(doc){
  if(doc.type == 'usertoken'){
      emit(doc.user_id, doc);
  }
}
""")

"""The state from their ids"""
redirect_uris = ViewDefinition('fxa_oauth_redirect_uris', 'by_state', """
function(doc){
  if(doc.type == 'fxa_oauth_redirect_uri'){
      emit(doc.state, doc);
  }
}
""")

"""The state from their ids"""
states = ViewDefinition('fxa_oauth_states', 'by_session_id', """
function(doc){
  if(doc.type == 'fxa_oauth_states'){
      emit(doc.session_id, doc);
  }
}
""")

"""The access_token from their ids"""
access_tokens = ViewDefinition('fxa_oauth_access_tokens', 'by_session_id', """
function(doc){
  if(doc.type == 'fxa_oauth_access_tokens'){
      emit(doc.session_id, doc);
  }
}
""")

l = locals().values()
docs = [v for v in l if isinstance(v, ViewDefinition)]
