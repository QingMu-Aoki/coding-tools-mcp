from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

import jwt

from coding_tools_mcp.oauth import (
    OAuthClientRegistry,
    OAuthConfig,
    create_access_token,
    create_refresh_token,
    validate_access_token,
    validate_refresh_token,
)


class OAuthRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.registry_path = os.path.join(self.tmp.name, "oauth_clients.json")
        self.env = patch.dict(
            os.environ,
            {"CODING_TOOLS_MCP_OAUTH_CLIENT_REGISTRY": self.registry_path},
            clear=False,
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def test_dynamic_public_client_survives_registry_restart(self) -> None:
        registry = OAuthClientRegistry()
        response = registry.register(
            {
                "redirect_uris": ["http://127.0.0.1/callback"],
                "token_endpoint_auth_method": "none",
            }
        )
        client_id = response["client_id"]

        reloaded = OAuthClientRegistry()
        self.assertIsNotNone(reloaded.get(client_id))
        self.assertTrue(reloaded.accepts_redirect(client_id, "http://127.0.0.1/callback"))

    def test_confidential_client_secret_digest_survives_restart(self) -> None:
        registry = OAuthClientRegistry()
        response = registry.register(
            {
                "redirect_uris": ["https://client.example/callback"],
                "token_endpoint_auth_method": "client_secret_post",
            }
        )
        client_id = response["client_id"]
        client_secret = response["client_secret"]

        with open(self.registry_path, encoding="utf-8") as handle:
            persisted = json.loads(handle.read())
        self.assertNotIn(client_secret, json.dumps(persisted))

        reloaded = OAuthClientRegistry()
        self.assertTrue(reloaded.authenticates(client_id, client_secret, "client_secret_post"))

    def test_refresh_rotation_preserves_absolute_expiry(self) -> None:
        registry = OAuthClientRegistry()
        response = registry.register(
            {
                "redirect_uris": ["http://127.0.0.1/callback"],
                "token_endpoint_auth_method": "none",
            }
        )
        client_id = response["client_id"]
        config = OAuthConfig(
            password="test",
            server_url="https://mcp.example",
            token_secret=b"test-secret-for-unit-tests",
            refresh_token_ttl=3600,
            registry=registry,
        )

        now = int(time.time())
        with patch("coding_tools_mcp.oauth.time.time", return_value=now):
            first = create_refresh_token(config, "https://mcp.example", client_id=client_id)
        first_claims = jwt.decode(
            first,
            config.token_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_exp": False},
        )

        with patch("coding_tools_mcp.oauth.time.time", return_value=now + 300):
            rotated = create_refresh_token(
                config,
                "https://mcp.example",
                client_id=client_id,
                expires_at=first_claims["exp"],
            )
        rotated_claims = jwt.decode(
            rotated,
            config.token_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_exp": False, "verify_iat": False},
        )
        self.assertEqual(first_claims["exp"], rotated_claims["exp"])

    def test_access_and_refresh_tokens_are_not_interchangeable(self) -> None:
        registry = OAuthClientRegistry()
        response = registry.register(
            {
                "redirect_uris": ["http://127.0.0.1/callback"],
                "token_endpoint_auth_method": "none",
            }
        )
        client_id = response["client_id"]
        config = OAuthConfig(
            password="test",
            server_url="https://mcp.example",
            token_secret=b"test-secret-for-unit-tests",
            registry=registry,
        )
        access = create_access_token(config, "https://mcp.example", client_id=client_id)
        refresh = create_refresh_token(config, "https://mcp.example", client_id=client_id)

        self.assertTrue(validate_access_token(access, config, "https://mcp.example"))
        self.assertFalse(validate_access_token(refresh, config, "https://mcp.example"))
        self.assertIsNotNone(validate_refresh_token(refresh, config, "https://mcp.example"))
        self.assertIsNone(validate_refresh_token(access, config, "https://mcp.example"))


if __name__ == "__main__":
    unittest.main()
