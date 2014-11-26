# Default value for configurable ENV variables
OAUTH_URI=${OAUTH_URI-https://oauth-stable.dev.lcip.org/v1}
SERVER_URI=${SERVER_URI-http://localhost:8000}
CLIENT_ID=${CLIENT_ID-d61805f6023398a3}
REDIRECT_URI=${REDIRECT_URI-http://localhost/}

SESSION_FILE=/tmp/user1

# 1. Get the state
http POST "${SERVER_URI}/tokens/fxa-oauth/params" redirect_uri=${REDIRECT_URI} --session="${SESSION_FILE}" -v

echo "Now enter the STATE: "
read STATE
echo "Ok STATE is: ${STATE}"

# 2. Starts the OAUTH process
http GET "${OAUTH_URI}/authorization?client_id=${CLIENT_ID}&state=${STATE}&scope=profile&action=signin" -v

echo "Click on that location link ^"

echo "Enter code: "
read CODE
echo "Ok CODE is: ${CODE}"

# 3. Finish the process and get back the hawk ID
http POST "${SERVER_URI}/tokens/fxa-oauth/token" state="${STATE}" code="${CODE}" --session="${SESSION_FILE}" -v

rm "${SESSION_FILE}"
