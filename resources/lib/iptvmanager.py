import socket
import json

import xbmc
from resources.lib.ipwww_video import channel_list, get_epg
from resources.lib.ipwww_common import addonid, utf8_quote_plus, ADDON


# IPTVManager class from https://github.com/add-ons/service.iptv.manager/wiki/Integration
class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager"""

        chan_list = []
        mode = '203' if ADDON.getSetting('streams_autoplay') == 'true' else '123'

        for id, name, _ in channel_list[:4]:
            iconimage = 'resource://resource.images.iplayerwww/media/' + id + '.png'
            url = ''.join((
                'plugin://', addonid,
                '?url=', utf8_quote_plus(id),
                '&mode=', mode,
                '&name=', utf8_quote_plus(name),
                '&iconimage', utf8_quote_plus(iconimage)
            ))
            chan_list.append({'id': 'ipwww.' + id, 'name': name, 'logo': iconimage, 'stream': url})
        return {'version': 1, 'streams': chan_list}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        return get_epg()


def channels(port):
    try:
        xbmc.log("[ipwww_video] [Info] iptvmanager requested channels on port {}".format(port), xbmc.LOGERROR)
        IPTVManager(int(port)).send_channels()
    except Exception as err:
        # Catch all errors to prevent codequick showing an error message
        xbmc.log("[ipwww_video] [Info] Error in iptvmanager.channels: {!r}.".format(err), xbmc.LOGERROR)


def epg(port):
    try:
        xbmc.log("[ipwww_video] [Info] iptvmanager requested epg data on port {}".format(port), xbmc.LOGERROR)
        IPTVManager(int(port)).send_epg()
    except Exception as err:
        # Catch all errors to prevent codequick showing an error message
        xbmc.log("[ipwww_video] [Info] Error in iptvmanager.epg: {!r}.".format(err), xbmc.LOGERROR)
