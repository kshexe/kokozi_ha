"""Config flow for Kokozi."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KokoziApiClient, KokoziAuthError, KokoziCannotConnect, get_jwt_subject
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_EXPIRES_IN,
    CONF_ISSUES_AT,
    CONF_LOGIN_PROVIDER,
    CONF_LOGIN_URL,
    CONF_OWNER_ID,
    CONF_POLLING_INTERVAL,
    CONF_REFRESH_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_TYPE,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    LOGGER,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
    LOGIN_PROVIDER_EMAIL,
)

EMAIL_LOGIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class KokoziConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kokozi."""

    VERSION = 1

    _login_provider: str = ""
    _login_url: str = ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return KokoziOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Log in directly with an email/password pair."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = KokoziApiClient(async_get_clientsession(self.hass))
            try:
                token = await client.async_login_with_email(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except KokoziCannotConnect:
                LOGGER.warning("Kokozi email login failed: cannot connect")
                errors["base"] = "cannot_connect"
            except KokoziAuthError as err:
                LOGGER.warning("Kokozi email login failed: %s", err)
                errors["base"] = "invalid_auth"
            except Exception:
                LOGGER.exception("Unexpected exception during Kokozi email login")
                errors["base"] = "unknown"
            else:
                self._login_provider = LOGIN_PROVIDER_EMAIL
                return await self._async_create_entry_from_token(token)

        return self.async_show_form(
            step_id="user", data_schema=EMAIL_LOGIN_SCHEMA, errors=errors
        )

    async def _async_create_entry_from_token(self, token) -> ConfigFlowResult:
        """Finish the flow by creating a config entry from a token response."""
        await self.async_set_unique_id("kokozi")
        self._abort_if_unique_id_configured()
        LOGGER.info(
            "Kokozi login succeeded: provider=%s token_type=%s expires_in=%s expires_at=%s refresh_expires_at=%s has_refresh_token=%s",
            self._login_provider,
            token.token_type,
            token.expires_in,
            token.expires_at,
            token.refresh_expires_at,
            token.refresh_token is not None,
        )
        return self.async_create_entry(
            title="Kokozi",
            data={
                CONF_ACCESS_TOKEN: token.access_token,
                CONF_REFRESH_TOKEN: token.refresh_token,
                CONF_TOKEN_TYPE: token.token_type,
                CONF_EXPIRES_IN: token.expires_in,
                CONF_ISSUES_AT: token.issues_at,
                CONF_EXPIRES_AT: token.expires_at,
                CONF_REFRESH_EXPIRES_AT: token.refresh_expires_at,
                CONF_OWNER_ID: get_jwt_subject(token.access_token),
                CONF_LOGIN_PROVIDER: self._login_provider,
                CONF_LOGIN_URL: self._login_url,
            },
        )

class KokoziOptionsFlow(OptionsFlowWithReload):
    """Handle Kokozi options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Kokozi options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLLING_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
                        ),
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=MIN_POLLING_INTERVAL,
                                max=MAX_POLLING_INTERVAL,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                                unit_of_measurement=UnitOfTime.SECONDS,
                            )
                        ),
                        vol.Coerce(int),
                    )
                }
            ),
        )
