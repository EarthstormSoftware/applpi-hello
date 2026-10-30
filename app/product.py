"""Juggle Hello: the example Juggle OS app on App Base, and the starting point for new ones.

App Base (base/) does the page's Device and MQTT tabs, the settings, the API, MQTT and Home Assistant, and asks
Juggle OS for what the OS owns (the Pi's name, Wi-Fi, setup mode, the clock). This is what's Hello's own: one setting,
a greeting, shown on its page, on its MQTT state topic and in Home Assistant, and changed from any of them.
"""
import json
from pathlib import Path

from base.settings import Setting, is_text

NAME = 'Hello'
VERSION = json.loads((Path(__file__).parent / 'app.json').read_text(encoding='utf-8'))['version']

GREETING_LONGEST = 64

SETTINGS = {
    'hello': {
        'greeting': Setting('Hello from Juggle OS', is_text(GREETING_LONGEST, allow_empty=False)),
    },
}

# Home Assistant: the greeting, as a text box
HA_ENTITIES = (('text', 'greeting'),)


def info(device):
    return {'greeting': device.settings.get('hello', 'greeting')}


def state(device):
    """The state topic (<topic base>/state)."""
    return {'greeting': device.settings.get('hello', 'greeting')}


def set(device, command):
    """A command on the set topic (<topic base>/set): {"greeting": "..."}."""
    if any(key != 'greeting' for key in command):
        return 'only greeting can be set'
    error, changed = device.settings.update({'hello': command})
    if not error:
        device.applied(changed)
    return error


def applied(device, changed):
    # A new greeting from the page, the API or MQTT: the state topic says so
    if any(section == 'hello' for section, _ in changed):
        device.state_changed()


def ha_entity(device, key, t):
    return {'name': 'Greeting', 'icon': 'mdi:hand-wave', 'max': GREETING_LONGEST,
            'value_template': '{{ value_json.greeting }}',
            'command_topic': t['set'], 'command_template': '{"greeting": {{ value | tojson }}}'}
