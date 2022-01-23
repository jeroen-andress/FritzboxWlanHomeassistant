from __future__ import annotations

import logging, hashlib, xml.etree.ElementTree as ET, asyncio, aiohttp, pickle, os

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME)
import homeassistant.helpers.config_validation as cv
import voluptuous

_LOGGER = logging.getLogger(__name__)

CONF_FRITZBOXURL = "url"
CONF_PASSWORD = "password"
CONF_SSID = "ssid"
PERSISTENT_FILE = os.path.join(os.path.dirname(__file__), "persistent.p")
DEFAULT_FRITZBOXURL = "http://fritz.box"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    voluptuous.Optional(CONF_FRITZBOXURL, default=DEFAULT_FRITZBOXURL): cv.string,
    voluptuous.Required(CONF_PASSWORD): cv.string,
    voluptuous.Required(CONF_SSID): cv.string
})

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    add_entities([FritzBox7412WLANSwitch(url=config.get(CONF_FRITZBOXURL) , password=config.get(CONF_PASSWORD), ssid=config.get(CONF_SSID))])

class FritzBox7412WLANSwitch(SwitchEntity):
    def __init__(self, url, password, ssid) -> None:
        self._url, self._password, self._ssid = url, password, ssid
        self._state = self._load_state()
        _LOGGER.warning(f"{self.name} created with hostname {self._hostname}, ssid {self._ssid} and init state {self._state}")
        super().__init__()

    @property
    def is_on(self):
        return self._state

    @property
    def icon(self):
        return "mdi:wifi-strength-3" if self.is_on else "mdi:wifi-strength-off-outline"

    @property
    def name(self):
        return "WLAN FRITZ!Box 7412"

    @property
    def _hostname(self):
        return self._url if self._url.startswith("http://") else f"http://{self._url}"

    def turn_on(self, **kwargs) -> None:
        asyncio.run(self.async_turn_on())

    def turn_off(self, **kwargs):
        asyncio.run(self.async_turn_off())

    def toggle(self, **kwargs):
        asyncio.run(self.async_toggle())

    async def async_turn_on(self, **kwargs):
        await self._switch_to_target_state(True)

    async def async_turn_off(self, **kwargs):
        await self._switch_to_target_state(False)
        
    async def async_toggle(self, **kwargs):
        await self._switch_to_target_state(not self.is_on)

    async def async_update(self):
        return self.is_on

    async def _switch_to_target_state(self, target_state: bool):
        if self.is_on != target_state:
            await self._update_wlan_state(target_state)
            self._dump_state(target_state)
            self._state = target_state

    async def _request_login(self, session, response=None):
        url = f"{self._hostname}/login_sid.lua{'' if response is None else f'?response={response}'}"

        async with session.get(url) as get_response:
            root = ET.fromstring(await get_response.text())
            SID = root.findall('SID')[0].text
            challenge = root.findall('Challenge')[0].text
            blocktime = root.findall('BlockTime')[0].text

            return SID, challenge, blocktime

    async def _get_session_id(self, session, password):
        SID, challenge, blocktime = await self._request_login(session)

        await asyncio.sleep(int(blocktime))

        if SID == '0000000000000000':
            response = f"{challenge}-{hashlib.md5(f'{challenge}-{password}'.encode('UTF-16LE')).hexdigest()}"
            SID, _, _ = await self._request_login(session, response)
        
        return SID

    async def _update_wlan_state(self, state: bool):
        async with aiohttp.ClientSession() as session:
            SID = await self._get_session_id(session, self._password)	
            url = f'{self._hostname}/data.lua'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {'xhr': '1', 'sid': SID, 'lang': 'de', 'no_sidrenew': '', 'apply': '', 'oldpage': '/wlan/wlan_settings.lua'}

            if state:
                payload.update({'active': 'on', 'SSID': self._ssid, 'hidden_ssid': 'on'})

            await session.post(url, headers=headers, data=payload)
            await session.get(f'{self._hostname}/login_sid.lua?logout=1&sid={SID}')

    def _dump_state(self, state: bool):
        pickle.dump(state, open(PERSISTENT_FILE, "wb"))

    def _load_state(self) -> bool:
        try:
            return pickle.load(open(PERSISTENT_FILE, "rb"))
        except:
            return False
