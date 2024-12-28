import socket
import json
from datetime import datetime, timedelta, timezone

import xbmc

from resources.lib.ipwww_video import (
    channel_list as tv_channel_list,
    SelectSynopsis,
    SelectImage)
from resources.lib.ipwww_radio import (
    ScrapeJSON as ScrapeSoundsJson,
    channel_list as radio_channel_list)
from resources.lib.ipwww_common import (
    addonid,
    utf8_quote_plus,
    ADDON,
    OpenRequest)


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
        tv_chans = enabled_channels(ADDON.getSetting('iptv.tv_channels').split(';'),
                                    tv_channel_list)
        radio_chans = enabled_channels(ADDON.getSetting('iptv.radio_channels').split(';'),
                                       radio_channel_list)
        return {'version': 1, 'streams': tv_chans + radio_chans}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        guide = tv_epg()
        guide.update(radio_epg())
        return {'version': 1, 'epg': guide}


def channels(port):
    xbmc.log(f"[ipwww_iptv] Sending IPTV channels list.", xbmc.LOGDEBUG)
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
        xbmc.log(f"[ipwww_iptv] Error in iptvmanager.epg: {err!r}.", xbmc.LOGDEBUG)


def enabled_channels(enabled_ids, all_channels):
    if all_channels is radio_channel_list:
        mode = '213'
    else:
        mode = '203'
    # BBC Two England has the same channel ID as BBC TWO (HD) and is filtered out to
    # prevent both appearing in the TV list when BBC Two is enabled.
    enabled_chans = [chan for chan in all_channels if chan[0] in enabled_ids and chan[1] != 'BBC Two England']
    chan_list = []
    for chan in enabled_chans:
        chan_id = chan[0]
        chan_name = chan[1]
        iconimage = f'resource://resource.images.iplayerwww/media/{chan_id}.png'
        url = ''.join((
            'plugin://', addonid,
            '?url=', utf8_quote_plus(chan_id),
            '&mode=', mode,
            '&name=', utf8_quote_plus(chan_name),
            '&iconimage', utf8_quote_plus(iconimage)
        ))
        chan_list.append(
            {'id': 'ipwww.' + chan_id,
             'name': chan_name,
             'logo': iconimage,
             'stream': url,
             'radio': all_channels is radio_channel_list}
        )
    return chan_list


def tv_epg():
    """Return the full TV EPG from 7 days back to 7 days ahead.

    """
    utc_now = datetime.now(timezone.utc)
    week_back = utc_now - timedelta(days=7)
    enabled_chan_ids = ADDON.getSetting('iptv.tv_channels').split(';')
    items_per_page = 200        # max allowed number
    tv_guide = {}
    xbmc.log(f"[ipwww_iptv] Creating IPTV EPG for channels {enabled_chan_ids}.", xbmc.LOGDEBUG)

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

        tv_guide['ipwww.' + chan_id] = progr_list
    return tv_guide


def get_next_revision():
    """Request a html page from a radio station to get the current _next revision."""
    data = ScrapeSoundsJson('https://www.bbc.co.uk/sounds/schedules/bbc_radio_one')
    return data['buildId']


def parse_radio_programme(programme):
    """Parse a single programme from a radio schedule and return a dict in the
    format required by IPTV Manager.

    """
    titles = programme['titles']
    playable = programme.get('playable_item')
    if playable:
        release_date = playable.get('release', {}).get('date')
        episode_id = playable['urn'].split(':')[-1]
        url = 'https://www.bbc.co.uk/sounds/play/' + episode_id
        stream = ''.join(('plugin://',
                          addonid,
                          '?url=', utf8_quote_plus(url),
                          '&mode=212'))  # &iconimage=&description=
    else:
        release_date = None
        stream = None

    return {
        'start': programme['start'],
        'stop': programme['end'],
        'title': titles.get('primary') or titles.get('secondary') or titles.get('tertiary'),
        'description': SelectSynopsis(programme.get('synopses')),
        'subtitle': programme.get('editorial_subtitle') or programme.get('subtitle'),
        'image': programme.get('image_url', '').replace('{recipe}', '832x468'),
        'date': release_date,
        'stream': stream
    }


def radio_epg():
    """Return the EPG of all enabled radio channels from 1 week ago up to next week."""
    utc_now = datetime.now(timezone.utc)
    enabled_chan_ids = ADDON.getSetting('iptv.radio-channels').split(';')
    # Create a list of dates from one week back to next week.
    dates_list = [(utc_now + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(-7, 8)]
    _next_revision = get_next_revision()
    radio_guide = {}
    for chan_id in enabled_chan_ids:
        last_start_time = ''
        programme_list = []
        for date in dates_list:
            url = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/{chan_id}/{date}.json'
            data = json.loads(OpenRequest('get', url))
            schedules = data['pageProps']['dehydratedState']['queries'][1]['state']['data']['data'][0]['data']
            # The first programme of a day can be the same as the last of the previous day.
            if schedules[0]['start'] == last_start_time:
                schedules = schedules[1:]
            programme_list.extend(parse_radio_programme(progr) for progr in schedules)
            last_start_time = programme_list[-1]['start']
        radio_guide['ipwww.' + chan_id] = programme_list
    return radio_guide
