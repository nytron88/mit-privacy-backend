import json
from flask import _request_ctx_stack, request, current_app
from functools import wraps
from jose import jwt
from six.moves.urllib.request import urlopen
from typing import Dict

ALGORITHMS = ["RS256"]

def requires_auth(func):
    """Determines if the access token is valid
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://" + current_app.config['OAUTH2_PROVIDER_DOMAIN'] + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError as jwt_error:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401) from jwt_error
        if unverified_header["alg"] == "HS256":
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=current_app.config['OAUTH2_PROVIDER_AUDIENCE'],
                    issuer="https://" + current_app.config['OAUTH2_PROVIDER_DOMAIN'] + "/"
                )
            except jwt.ExpiredSignatureError as expired_sign_error:
                raise AuthError({"code": "token_expired",
                                 "description": "token is expired"}, 401) from expired_sign_error
            except jwt.JWTClaimsError as jwt_claims_error:
                raise AuthError({"code": "invalid_claims",
                                 "description":
                                     "incorrect claims,"
                                     " please check the audience and issuer"}, 401) from jwt_claims_error
            except Exception as exc:
                raise AuthError({"code": "invalid_header",
                                 "description":
                                     "Unable to parse authentication"
                                     " token."}, 401) from exc

            _request_ctx_stack.top.current_user = payload
            return func(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)

    return decorated

# Format error response and append status code.
class AuthError(Exception):
    """
    An AuthError is raised whenever the authentication failed.
    """

    def __init__(self, error: Dict[str, str], status_code: int):
        super().__init__()
        self.error = error
        self.status_code = status_code


def get_token_auth_header() -> str:
    """Obtains the access token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must start with"
                             " Bearer"}, 401)
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                         "description": "Token not found"}, 401)
    if len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must be"
                             " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_scope(required_scope: str) -> bool:
    """Determines if the required scope is present in the access token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("permissions"):
        token_scopes = unverified_claims["permissions"]
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False

def get_user_permissions():
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    permissions = unverified_claims["permissions"]
    
    return permissions