import socket
import json
from datetime import datetime, timedelta, timezone

import xbmc

from resources.lib.ipwww_video import channel_list as tv_channel_list, SelectSynopsis, SelectImage
from resources.lib.ipwww_common import addonid, utf8_quote_plus, ADDON, OpenRequest


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

        for chan_id, chan_name, _ in enabled_tv_channels():
            iconimage = f'resource://resource.images.iplayerwww/media/{chan_id}.png'
            url = ''.join((
                'plugin://', addonid,
                '?url=', utf8_quote_plus(chan_id),
                '&mode=', mode,
                '&name=', utf8_quote_plus(chan_name),
                '&iconimage', utf8_quote_plus(iconimage)
            ))
            chan_list.append({'id': 'ipwww.' + chan_id, 'name': chan_name, 'logo': iconimage, 'stream': url})
        return {'version': 1, 'streams': chan_list}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        return get_epg()


def channels(port):
    try:
        IPTVManager(int(port)).send_channels()
    except Exception as err:
        # Catch all errors to prevent default() showing an error message
        xbmc.log(f"[ipwww_iptv] Error in iptvmanager.channels: {err!r}.", xbmc.LOGERROR)


def epg(port):
    try:
        IPTVManager(int(port)).send_epg()
    except Exception as err:
        # Catch all errors to prevent default() showing an error message
        xbmc.log(f"[ipwww_iptv] Error in iptvmanager.epg: {err!r}.", xbmc.LOGERROR)


def enabled_tv_channels():
    enabled_chan_ids = ADDON.getSetting('iptv.tv-channels').split(';')
    # BBC Two England has the same channel ID as BBC TWO (HD) and is filtered out to
    # prevent both appearing in the TV list if BBC Two is enabled.
    return [chan for chan in tv_channel_list if chan[0] in enabled_chan_ids and chan[1] != 'BBC Two England']


def get_epg(chan_list=None):
    """Get the full EPG from 7 days back to 7 days ahead.

    """
    utc_now = datetime.now(timezone.utc)
    week_back = utc_now - timedelta(days=7)
    enabled_chan_ids = ADDON.getSetting('iptv.channels').split(';')
    items_per_page = 200        # max allowed number
    epg = {}

    for chan_id in enabled_chan_ids:
        # There are no schedules specifically for HD channels.
        if chan_id == 'bbc_one_hd':
            schedule_chan_id = 'bbc_one_london'
        elif chan_id.endswith('_hd'):
            schedule_chan_id = chan_id[:-3]
        elif chan_id:
            schedule_chan_id = chan_id
        else:
            continue

        progr_list = []
        # Range is just to ensure we break out of the loop at some point if something goes
        # wrong with counting received items. Schedules should never have more than 2000
        # items in 2 weeks.
        for pagenr in range(1, 10):
            url = ''.join(('https://ibl.api.bbc.co.uk/ibl/v1/channels/',
                           schedule_chan_id,
                           '/broadcasts?per_page=',
                           str(items_per_page),
                           '&page=',
                           str(pagenr),
                           '&from_date=',
                           week_back.strftime('%Y-%m-%dT%H:%M')))
            resp_data = json.loads(OpenRequest('get', url))
            schedule_list = resp_data['broadcasts']['elements']
            for progr in schedule_list:
                episode = progr['episode']
                categories = episode.get('categories')
                if episode.get('status') == 'available':
                    url = 'https://www.bbc.co.uk/iplayer/episode/' + episode['id']
                    stream = ''.join(('plugin://',
                                      addonid,
                                      '?url=', utf8_quote_plus(url),
                                      '&mode=202'))  # &iconimage=&description=
                else:
                    stream = None
                progr_list.append({
                    'start': progr['scheduled_start'],
                    'stop': progr['scheduled_end'],
                    'title': episode.get('title'),
                    'description': SelectSynopsis(episode.get('synopses')),
                    'subtitle': episode.get('editorial_subtitle') or episode.get('subtitle'),
                    'genre': categories[0] if categories else None,
                    'image': SelectImage(episode.get('images')),
                    'date': episode.get('release_date_time'),
                    'stream': stream
                })
            if pagenr * items_per_page >= resp_data['broadcasts']['count']:
                break

        epg['ipwww.' + chan_id] = progr_list
    return {'version': 1, 'epg': epg}