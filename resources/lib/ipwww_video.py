# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
import re
import datetime
import time
import json

from datetime import timedelta
from operator import itemgetter

from resources.lib.ipwww_common import (
    translation, AddMenuEntry, OpenURL, OpenRequest, CheckLogin, CreateBaseDirectory,
    GetCookieJar, ParseImageUrl, download_subtitles, GeoBlockedError, WebRequestError,
    duration_2_secs, PostJson, strptime, addonid, DeleteUrl, ProgressDlg, utf8_quote_plus)
from resources.lib import ipwww_progress

import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
from random import randint

ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')


def tp(path):
    return xbmcvfs.translatePath(path)


def RedButtonDialog():
    if ADDON.getSetting('redbutton_warning') == 'true':
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(translation(30405), translation(30406) + "\n" + translation(30407),
                           translation(30409), translation(30408))
        if ret:
            ListRedButton()
    else:
        ListRedButton()


def ListRedButton():
    channel_list = [
        ('sport_stream_01',  'BBC Red Button 1'),
        ('sport_stream_02',  'BBC Red Button 2'),
        ('sport_stream_03',  'BBC Red Button 3'),
        ('sport_stream_04',  'BBC Red Button 4'),
        ('sport_stream_05',  'BBC Red Button 5'),
        ('sport_stream_06',  'BBC Red Button 6'),
        ('sport_stream_07',  'BBC Red Button 7'),
        ('sport_stream_08',  'BBC Red Button 8'),
        ('sport_stream_09',  'BBC Red Button 9'),
        ('sport_stream_10',  'BBC Red Button 10'),
        ('sport_stream_11',  'BBC Red Button 11'),
        ('sport_stream_12',  'BBC Red Button 12'),
        ('sport_stream_13',  'BBC Red Button 13'),
        ('sport_stream_14',  'BBC Red Button 14'),
        ('sport_stream_15',  'BBC Red Button 15'),
        ('sport_stream_16',  'BBC Red Button 16'),
        ('sport_stream_17',  'BBC Red Button 17'),
        ('sport_stream_18',  'BBC Red Button 18'),
        ('sport_stream_19',  'BBC Red Button 19'),
        ('sport_stream_20',  'BBC Red Button 20'),
        ('sport_stream_21',  'BBC Red Button 21'),
        ('sport_stream_22',  'BBC Red Button 22'),
        ('sport_stream_23',  'BBC Red Button 23'),
        ('sport_stream_24',  'BBC Red Button 24'),
        ('sport_stream_01b', 'BBC Red Button 1b'),
        ('sport_stream_02b', 'BBC Red Button 2b'),
        ('sport_stream_03b', 'BBC Red Button 3b'),
        ('sport_stream_04b', 'BBC Red Button 4b'),
        ('sport_stream_05b', 'BBC Red Button 5b'),
        ('sport_stream_06b', 'BBC Red Button 6b'),
        ('sport_stream_07b', 'BBC Red Button 7b'),
        ('sport_stream_08b', 'BBC Red Button 8b'),
        ('sport_stream_09b', 'BBC Red Button 9b'),
        ('sport_stream_10b', 'BBC Red Button 10b'),
        ('sport_stream_11b', 'BBC Red Button 11b'),
        ('sport_stream_12b', 'BBC Red Button 12b'),
        ('sport_stream_13b', 'BBC Red Button 13b'),
        ('sport_stream_14b', 'BBC Red Button 14b'),
        ('sport_stream_15b', 'BBC Red Button 15b'),
        ('sport_stream_16b', 'BBC Red Button 16b'),
        ('sport_stream_17b', 'BBC Red Button 17b'),
        ('sport_stream_18b', 'BBC Red Button 18b'),
        ('sport_stream_19b', 'BBC Red Button 19b'),
        ('sport_stream_20b', 'BBC Red Button 20b'),
        ('sport_stream_21b', 'BBC Red Button 21b'),
        ('sport_stream_22b', 'BBC Red Button 22b'),
        ('sport_stream_23b', 'BBC Red Button 23b'),
        ('sport_stream_24b', 'BBC Red Button 24b'),
    ]
    iconimage = tp('special://home/addons/plugin.video.iplayerwww/media/red_button.png')
    for id, name in channel_list:
        mode = 203 if ADDON.getSetting('streams_autoplay') == 'true' else 123
        AddMenuEntry(name, mode, iconimage,
                     callb_kwargs=dict(name=name, channelname=id, iconimage=iconimage))


def ListUHDTrial():
    channel_list = [
        ('uk_bbc_stream_041',  'UHD Trial 1'),
        ('uk_bbc_stream_042',  'UHD Trial 2'),
        ('uk_bbc_stream_043',  'UHD Trial 3'),
        ('uk_bbc_stream_044',  'UHD Trial 4'),
        ('uk_bbc_stream_045',  'UHD Trial 5'),
    ]
    iconimage = 'resource://resource.images.iplayerwww/media/red_button.png'
    for id, name in channel_list:
        AddMenuEntry(name, 205, iconimage, callb_kwargs=dict(name=name, channelname=id))


def AddAvailableUHDTrialItem(name, channelname):
    # source = int(ADDON.getSetting('live_source'))
    # if (source == 1):
    #     provider = "ak"
    # elif (source == 2):
    #     provider = "llnw"
    # else:
    #     provider = "ak"

    url = f'https://ve-uhd-push-uk.live.fastly.md.bbci.co.uk/x=4/i=urn:bbc:pips:service:{channelname}/iptv_uhd_v1.mpd'
    # url = "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/webcast/dash/uk/full/%s/%s.mpd" % (provider,channelname)

    PlayStream(url)


channel_list = [
        ('bbc_one_hd',                       'BBC One',                  'bbc_one_london'),
        ('bbc_two_england',                  'BBC Two',                  'bbc_two_england'),
        ('bbc_three_hd',                     'BBC Three',                'bbc_three'),
        ('bbc_four_hd',                      'BBC Four',                 'bbc_four'),
        ('cbbc_hd',                          'CBBC',                     'cbbc'),
        ('cbeebies_hd',                      'CBeebies',                 'cbeebies'),
        ('bbc_news24',                       'BBC News Channel',         'bbc_news24'),
        ('bbc_parliament',                   'BBC Parliament',           'bbc_parliament'),
        ('bbc_alba',                         'Alba',                     'bbc_alba'),
        ('bbc_scotland_hd',                  'BBC Scotland',             'bbc_scotland'),
        ('s4cpbs',                           'S4C',                      's4cpbs'),
        ('bbc_one_london',                   'BBC One London',           'bbc_one_london'),
        ('bbc_one_scotland_hd',              'BBC One Scotland',         'bbc_one_scotland'),
        ('bbc_one_northern_ireland_hd',      'BBC One Northern Ireland', 'bbc_one_northern_ireland'),
        ('bbc_one_wales_hd',                 'BBC One Wales',            'bbc_one_wales'),
        ('bbc_two_scotland',                 'BBC Two Scotland',         'bbc_two_england'),
        ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland', 'bbc_two_northern_ireland_digital'),
        ('bbc_two_wales_digital',            'BBC Two Wales',            'bbc_two_wales_digital'),
        ('bbc_two_england',                  'BBC Two England',          'bbc_two_england'),
        ('bbc_one_cambridge',                'BBC One Cambridge',        'bbc_one_london'),
        ('bbc_one_channel_islands',          'BBC One Channel Islands',  'bbc_one_london'),
        ('bbc_one_east',                     'BBC One East',             'bbc_one_london'),
        ('bbc_one_east_midlands',            'BBC One East Midlands',    'bbc_one_london'),
        ('bbc_one_east_yorkshire',           'BBC One East Yorkshire',   'bbc_one_london'),
        ('bbc_one_north_east',               'BBC One North East',       'bbc_one_london'),
        ('bbc_one_north_west',               'BBC One North West',       'bbc_one_london'),
        ('bbc_one_oxford',                   'BBC One Oxford',           'bbc_one_london'),
        ('bbc_one_south',                    'BBC One South',            'bbc_one_london'),
        ('bbc_one_south_east',               'BBC One South East',       'bbc_one_london'),
        ('bbc_one_south_west',               'BBC One South West',       'bbc_one_london'),
        ('bbc_one_west',                     'BBC One West',             'bbc_one_london'),
        ('bbc_one_west_midlands',            'BBC One West Midlands',    'bbc_one_london'),
        ('bbc_one_yorks',                    'BBC One Yorks',            'bbc_one_london'),
        ('red_button_one',                   'Red Button One',           '')
    ]


# ListLive creates menu entries for all live channels.
def ListLive():
    from urllib.parse import urlencode
    enabled_chans = ADDON.getSetting('enabled_tv_channels').split(';')
    enabled_chan_list = [chan for chan in channel_list if chan[0] in enabled_chans]
    schedules = GetSchedules(enabled_chan_list)
    for id, name, schedule_chan_id in enabled_chan_list:
        now_on, schedule = schedules.get(schedule_chan_id, ('', ''))
        title = '{}    [COLOR orange]{}[/COLOR]'.format(name, now_on)
        iconimage = 'resource://resource.images.iplayerwww/media/'+id+'.png'

        if ADDON.getSetting('streams_autoplay') == 'true':
            mode = 203
            restart_action = 'PlayMedia'
        else:
            mode = 123
            restart_action = "Container.Update"

        querystring = urlencode({'mode': mode,
                                 'name': name,
                                 'channelname': id,
                                 'iconimage': iconimage,
                                 'watch_from_start': 'True'})
        ctx_mnu = [(translation(30603),     # 'Watch from the start'
                    ''.join((restart_action, '(plugin://', addonid, '?', querystring,
                             ', noresume)' if mode == 203 else ')'))
                    )]
        AddMenuEntry(title, mode, iconimage, description=schedule, resume_time='0', context_mnu=ctx_mnu,
                     callb_kwargs=dict(name=title, channelname=id, iconimage=iconimage))
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
    sys.exit()


def ListAtoZ():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '0-9')]

    if int(ADDON.getSetting('scrape_atoz')) == 1:
        with ProgressDlg(translation(30319)) as pDialog:
            page = 1
            total_pages = len(characters)
            for name, url in characters:
                GetAtoZPage(url)
                percent = int(100*page/total_pages)
                pDialog.update(percent,translation(30319),name)
                page += 1
    else:
        for name, url in characters:
            AddMenuEntry(name, 124, callb_kwargs=dict(url=url))

def ListChannelAtoZ():
    """List programmes for each channel based on alphabetical order.

    Only creates the corresponding directories for each channel.
    """
    channel_list = [
        ('bbcone',           'bbc_one_hd',              'BBC One'),
        ('bbctwo',           'bbc_two_hd',              'BBC Two'),
        ('tv/bbcthree',      'bbc_three_hd',          'BBC Three'),
        ('bbcfour',          'bbc_four_hd',            'BBC Four'),
        ('tv/cbbc',          'cbbc_hd',                    'CBBC'),
        ('tv/cbeebies',      'cbeebies_hd',            'CBeebies'),
        ('tv/bbcnews',       'bbc_news24',     'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament',   'BBC Parliament'),
        ('tv/bbcalba',       'bbc_alba',                   'Alba'),
        ('tv/bbcscotland',   'bbc_scotland_hd',    'BBC Scotland'),
        ('tv/s4c',           's4cpbs',                      'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = 'resource://resource.images.iplayerwww/media/'+img+'.png'
        url = "https://www.bbc.co.uk/%s/a-z" % id
        AddMenuEntry(name, 128, iconimage, callb_kwargs=dict(page_url=url))


def GetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    current_url = 'https://www.bbc.co.uk/iplayer/a-z/%s' % url
    try:
        ScrapeEpisodes(current_url, True)
    except WebRequestError as err:
        # Ignore missing pages; there are simply no programmes starting with this letter.
        if err.status_code == 404:
            return
        else:
            raise


def GetMultipleEpisodes(url):
    GetEpisodes(url)


def ParseAired(aired):
    """Parses a string format %d %b %Y to %d/%n/%Y otherwise empty string."""
    if aired:
        try:
            # Need to use equivelent for datetime.strptime() due to weird TypeError.
            return datetime.datetime(*(time.strptime(aired[0], '%d %b %Y')[0:6])).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return ''


def FirstShownToAired(first_shown):
    """Converts the 'First shown' tag to %Y %m %d format."""
    release_parts = first_shown.split(' ')

    if len(release_parts) == 1:
        month = '01'
        day = '01'
        year = first_shown
    else:
        year = release_parts[-1]
        month = release_parts[-2]
        monthDict={
            'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
            'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
        if month in monthDict:
            month = monthDict[month]
            day = release_parts[-3].rjust(2,'0')
        else:
            month = '01'
            day = '01'
    aired = year + '-' + month + '-' + day
    return aired


def GetEpisodes(url):
    new_url = 'https://www.bbc.co.uk/iplayer/episodes/%s' % url
    ScrapeEpisodes(new_url)


def GetGroup(url):
    page_url = "https://www.bbc.co.uk/iplayer/group/" + url
    pages = [(GetJsonData(page_url), '')]
    pagination = pages[0][0].get('pagination')
    if pagination:
        total_pages = pagination.get('totalPages', 1)
        if total_pages > 1:
            pages.extend(MultiPageJson(page_url, range(1, total_pages)))
    for page_data, _ in pages:
        for episode_data in page_data['entities']['elements']:
            parse_group_item(episode_data, page_data['entities'].get('group', {}).get('title'))


def parse_group_item(episode_data: dict, group_name: str):
    """Parse an item from a group.

    All group content apears to be of type 'episode'. Some descriptions, however,
    obviously refer to the whole programme, rather than just one episode, while others
    definitely describe a particular episode. In groups like those from a category page,
    one would expect an item to be listed as a programme folder, but other groups may
    list various episodes from different programmes based on a common theme.

    This function attempts to decide whether an item should be displayed as a programme
    folder or as an episode, preferring programme folders whenever possible, but more
    importantly, trying to match the displayed item with its description.

    """
    if episode_data['type'] == 'episode':
        category = (episode_data.get('labels') or {}).get('category')
        synopses = episode_data.get('synopses', '')
        programme_type = episode_data.get('programme_type')
        if (programme_type == 'narrative'
                and category not in ('Documentary', )
                and 'editorial' in synopses):
            result = ParseEpisodeAsProgramme(episode_data)
            url = result.pop('url')
            AddMenuEntry(mode=128, callb_kwargs={'page_url': url}, **result)
        else:
            result = ParseEpisode(episode_data)
            programme_id = episode_data['tleo_id']
            if programme_id and episode_data['id'] != programme_id:
                result['context_mnu'] = [CtxMnuViewAllEpisodes(programme_id)]
            CheckAutoplay(**result)
    else:
        xbmc.log(f"[IPWWW_VIDEO] unsupported type '{episode_data['type']}' of '{episode_data['title']}' in group '{group_name}'.")


def MultiPageJson(url: str, page_range: range):
    from concurrent import futures

    base_url = re.sub(r'[?&]page=\d+', '', url, 1)
    if '?' in base_url:
        base_url += '&page='
    else:
        base_url += '?page='

    if len(page_range) == 1:
        # No need to set up a whole thread pool.
        url = base_url + str(page_range[0] + 1)
        return ((GetJsonData(url), url), )

    page_urls = [base_url + str(page_nr + 1) for page_nr in page_range]
    with futures.ThreadPoolExecutor(max_workers=16) as executor:
        res = [executor.submit(GetJsonData, url) for url in page_urls]
        futures.wait(res)
    return zip((r.result() for r in res), page_urls)


def ScrapeEpisodes(page_url, all_at_once=None):
    """Creates a list of programmes/episodes from a resource that consist of one or more
    pages.

    Parameter `all_at_once` determines whether to fetch a single page or all possible
    pages at once. The default (`None`) is to use the add-on setting `paginate_episodes`.
    If the resource has multiple pages and only a single page is requested, a 'Next Page'
    item will be added to the bottom of the list.

    :param page_url: The full url to the resource.
    :param all_at_once: Whether to fetch all possible pages at once.

    """
    if all_at_once is None:
        all_at_once = int(ADDON.getSetting('paginate_episodes')) == 1
    else:
        all_at_once = all_at_once in (True, 'True', 'true', 1, '1')

    pages = [(GetJsonData(page_url), page_url)]
    pagination = pages[0][0].get('pagination')
    if pagination:
        current_page = pagination.get('currentPage', 1)
        total_pages = pagination.get('totalPages', 1)

        if total_pages > 1 and all_at_once:
            pages.extend(MultiPageJson(page_url, range(1, total_pages)))
    else:
        total_pages = current_page = 1

    for page_data in pages:
        ParseJSON(*page_data)

    if not all_at_once and current_page < total_pages:
        base_url = re.sub(r'[?&]page=\d+', '', page_url, 1)
        if '?' in base_url:
            page_url = f'{base_url}&page={current_page + 1}'
        else:
            page_url = f'{base_url}?page={current_page + 1}'

        AddMenuEntry("[COLOR ffffa500]%s >>[/COLOR]" % translation(30320), 128,
                     item_position='bottom',
                     callb_kwargs=dict(page_url=page_url))


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.
    The category names are scraped from the website.
    """
    html = OpenURL('https://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="(/iplayer/[^"]+?)".*?categories-sub-nav__item.*?><span class="lnk__label">(.+?)</span>'
        ).findall(html)
    for url, name in match:
        if name in ("View all", "A-Z"):
            continue
        AddMenuEntry(name, 126, callb_kwargs=dict(url=url))


def ListCategoryFilters(url):
    """Parses the available category filters (if available) and creates directories for selcting them.
    If there are no filters available, all programmes will be listed using GetFilteredCategory.
    """
    url = url.split('/')[0]
    NEW_URL = 'https://www.bbc.co.uk/iplayer/categories/%s/a-z' % url

    # Read selected category's page.
    html = OpenURL(NEW_URL)
    # Some categories offer filters, we want to provide these filters as options.
    match1 = re.findall(
        '<a href="/iplayer/categories/(.+?)/a-z".*?>(.+?)</a>',
        html,
        re.DOTALL)
    if match1:
        AddMenuEntry('All', url, 126, callb_kwargs=dict(url=url))
        for url, name in match1:
            AddMenuEntry(name, url, 126, callb_kwargs=dict(url=url))
    else:
        GetFilteredCategory(url)


def GetFilteredCategory(url):
    """Parses the programmes available in the category view."""
    NEW_URL = 'https://www.bbc.co.uk' + url
    ScrapeEpisodes(NEW_URL)


def ListChannelHighlights():
    """Creates a list directories linked to the highlights section of each channel."""
    channel_list = [
        ('bbcone',           'bbc_one_hd',              'BBC One'),
        ('bbctwo',           'bbc_two_hd',              'BBC Two'),
        ('tv/bbcthree',      'bbc_three_hd',          'BBC Three'),
        ('bbcfour',          'bbc_four_hd',            'BBC Four'),
        ('tv/cbbc',          'cbbc_hd',                    'CBBC'),
        ('tv/cbeebies',      'cbeebies_hd',            'CBeebies'),
        ('tv/bbcnews',       'bbc_news24',     'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament',   'BBC Parliament'),
        ('tv/bbcalba',       'bbc_alba',                   'Alba'),
        ('tv/bbcscotland',   'bbc_scotland_hd',    'BBC Scotland'),
        ('tv/s4c',           's4cpbs',                      'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = 'resource://resource.images.iplayerwww/media/'+img+'.png'
        AddMenuEntry(name, 106, iconimage, callb_kwargs=dict(highlights_url=id))


def ParseSingleJSON(meta, item, name, added_playables, added_directories):
    main_url = None
    episodes_url = ''
    episodes_title = ''
    num_episodes = None
    synopsis = ''
    icon = ''
    aired = ''
    title = ''

    if 'episode' in item:
        # An episode in a programme/series folder
        CheckAutoplay(**ParseEpisode(item['episode'], is_standalone=False))
        return
    else:
        if 'count' in item:
            if item['count']>1:
                num_episodes = str(item['count'])
                if 'id' in item:
                    main_url = 'https://www.bbc.co.uk/iplayer/episodes/' + item.get('id')
            elif 'id' in item:
                main_url = 'https://www.bbc.co.uk/iplayer/episode/' + item.get('id')
        elif 'id' in item:
            if 'initial_children' in item:
                for ic in item['initial_children']:
                    if item.get('id') == ic['id']:
                        # This is just a playable, do not create a directory.
                        # Use the initial children to create the entry as it normally contains more information.
                        ParseSingleJSON(meta, ic, name, added_playables, added_directories)
                    else:
                        # Create a directory
                        episodes_url = 'https://www.bbc.co.uk/iplayer/episodes/' + item.get('id')
            else:
                main_url = 'https://www.bbc.co.uk/iplayer/episode/' + item.get('id')
        elif 'href' in item:
            # Some strings already contain the full URL, need to work around this.
            url = item['href'].replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
                if meta == 'tleo-item':
                    episodes_url = 'https://www.bbc.co.uk' + url
                    # print(episodes_url)
                else:
                    main_url = 'https://www.bbc.co.uk' + url

        if 'secondaryHref' in item:
            # Some strings already contain the full URL, need to work around this.
            url = item['secondaryHref'].replace('http://www.bbc.co.uk','')
            url = url.replace('https://www.bbc.co.uk','')
            if url:
                episodes_url = 'https://www.bbc.co.uk' + url
                episodes_title = item["title"]
        elif meta:
            if 'secondaryHref' in meta:
                # Some strings already contain the full URL, need to work around this.
                url = meta['secondaryHref'].replace('http://www.bbc.co.uk','')
                url = url.replace('https://www.bbc.co.uk','')
                if url:
                    episodes_url = 'https://www.bbc.co.uk' + url
                    episodes_title = item["title"]
            if 'episodesAvailable' in meta:
                if meta['episodesAvailable'] > 1:
                    num_episodes = str(meta['episodesAvailable'])

        if 'subtitle' in item:
            if 'title' in item:
                title = "%s - %s" % (item['title'], item['subtitle'])
            else:
                title = name
        elif 'title' in item:
            title = item['title']
        else:
            title = name

        if 'synopsis' in item:
            synopsis = item['synopsis']
        if 'synopses' in item:
            if 'editorial' in item['synopses']:
                synopsis = item['synopses']['editorial']
            elif 'large' in item['synopses']:
                synopsis = item['synopses']['large']
            elif 'medium' in item['synopses']:
                synopsis = item['synopses']['medium']
            elif 'small' in item['synopses']:
                synopsis = item['synopses']['small']

        if 'imageTemplate' in item:
            icon = item['imageTemplate'].replace("{recipe}","832x468")
        if 'images' in item:
            icon = item['images']['standard'].replace("{recipe}","832x468")
        elif 'sources' in item:
            temp = item['sources'][0]['srcset'].split()[0]
            icon = re.sub(r'ic/.+?/','ic/832x468/',temp)

    if num_episodes:
        if not main_url in added_directories:
            title = '[B]'+item['title']+'[/B] - '+num_episodes+' episodes available'
            AddMenuEntry(title, 139, icon, synopsis,
                         callb_kwargs=dict(page_url=main_url))
            added_directories.append(main_url)

    elif episodes_url:
        if not episodes_url in added_directories:
            if episodes_title=='':
                episodes_title = title
            AddMenuEntry('[B]%s[/B]' % (episodes_title), 128, icon, synopsis,
                         callb_kwargs=dict(page_url=episodes_url))
            added_directories.append(main_url)
    elif main_url:
        if not main_url in added_playables:
            CheckAutoplay(title , main_url, icon, synopsis, aired)
            added_playables.append(main_url)


def ParseJSON(programme_data, current_url):
    """Parses the JSON data containing programme information of a page. Contains a lot of fallbacks
    """

    added_playables = []
    added_directories = []

    if programme_data:
        name = ''
        if 'header' in programme_data:
            if 'title' in programme_data['header']:
                name = programme_data['header']['title']
            url_split = current_url.replace('&','?').split('?')
            is_paginated = False
            """ Avoid duplicate entries by checking if we are on page >1
            """
            for part in url_split:
                if part.startswith('page'):
                    is_paginated = True
            if not is_paginated:
                if 'availableSlices' in programme_data['header']:
                    current_series = programme_data['header']['currentSliceId']
                    slices = programme_data['header']['availableSlices']
                    if slices is not None:
                        for series in slices:
                            if series['id'] == current_series:
                                continue
                            base_url = url_split[0]
                            series_url = base_url + '?seriesId=' + series['id']
                            AddMenuEntry('[B]%s: %s[/B]' % (name, series['title']), 128,
                                         callb_kwargs=dict(page_url=series_url))

        programmes = None
        if 'currentLetter' in programme_data:
            # This must be an A-Z page.
            current_letter = programme_data['currentLetter']
            programmes = programme_data['programmes'][current_letter]['entities']
        elif 'entities' in programme_data:
            if 'elements' in programme_data['entities']:
                programmes = programme_data['entities']['elements']
            if 'results' in programme_data['entities']:
                programmes = programme_data['entities']['results']
        elif 'relatedEpisodes' in programme_data:
            if 'episodes' in programme_data['relatedEpisodes']:
                programmes = programme_data['relatedEpisodes']['episodes']
            if 'slices' in programme_data['relatedEpisodes']:
                if programme_data['relatedEpisodes']['slices'] is not None:
                    if 'episode' in programme_data:
                        if 'title' in programme_data['episode']:
                            name = programme_data['episode']['title']
                    url_split = current_url.replace('&','?').split('?')
                    current_series = programme_data['relatedEpisodes']['currentSliceId']
                    for series in programme_data['relatedEpisodes']['slices']:
                        if series['id'] == current_series:
                            continue
                        base_url = url_split[0]
                        series_url = base_url + '?seriesId=' + series['id']
                        AddMenuEntry('[B]%s: %s[/B]' % (name, series['title']['default']), 128,
                                     callb_kwargs=dict(page_url=series_url))
        elif 'items' in programme_data:
            # This must be Watchlist or Continue Watching.
            programmes = programme_data['items']

        if programmes:
            for item in programmes:
                meta = None
                if 'props' in item:
                    meta = item.get('meta')
                    item = item.get('props')
                elif 'contentItemProps' in item:
                    meta = item.get('type')
                    item = item.get('contentItemProps')
                item_type = item.get('type')
                if item_type == 'episode':
                    episode_dta = ParseEpisode(item)
                    if episode_dta:
                        CheckAutoplay(**episode_dta)
                elif item_type in ('programme', 'programme_large'):
                    is_playable, pgm_dta = ParseProgramme(item)
                    if is_playable:
                        CheckAutoplay(**pgm_dta)
                    else:
                        url = pgm_dta.pop('url')
                        AddMenuEntry(mode=128, **pgm_dta, callb_kwargs=dict(page_url=url))
                else:
                    ParseSingleJSON(meta, item, name, added_playables, added_directories)

        # The next section is for global and channel highlights. They are a bit tricky.
        groups = None
        highlights = None
        bundles = None
        if 'groups' in programme_data:
            groups = programme_data.get('groups')
            for entity in groups:
                title = entity.get('title')
                id = entity.get('id')
                if title and id:
                    # list the group folder
                    AddMenuEntry('[B]%s[/B]' % title, 127,
                                 description=translation(30314),
                                 callb_kwargs=dict(url=id))
                else:
                    # List the group's content
                    for item in entity['entities']:
                        if 'props' in item:
                            item = item.get("props")
                        ParseSingleJSON(None, item, None, added_playables, added_directories)

        if 'highlights' in programme_data:
            highlights = programme_data.get('highlights')
            entity = highlights.get("items")
            if entity:
                for item in entity:
                    if 'props' in item:
                        item = item.get("props")
                    parse_group_item(item, 'highlights')

        if 'bundles' in programme_data:
            bundles = programme_data.get('bundles')
            for bundle in bundles:
                title = bundle.get('title', {}).get('default')
                journey = bundle.get('journey')
                if journey:
                    id = journey.get('id')
                    type = journey.get('type')
                    if title:
                        if id and (type == 'group'):
                            AddMenuEntry('[B]%s[/B]' % title, 127,
                                         description=translation(30314),
                                         callb_kwargs=dict(url=id))
                        elif id and (type == 'category'):
                            cat_url = f"/iplayer/categories/{id}"
                            AddMenuEntry('[B]%s[/B]' % title, 126,
                                         description=translation(30314),
                                         callb_kwargs=dict(url=cat_url))
                else:
                    bundle_id = bundle.get('id')
                    if bundle_id == 'hero':
                        for item in bundle['entities']:
                            episode_data = ParseHeroItem(item.get('episode'))
                            if episode_data:
                                CheckAutoplay(**episode_data)
                    elif bundle_id:
                        # Use 198 - ListRecommendations() to parse the bundle's content from the original page.
                        AddMenuEntry('[B]%s[/B]' % title, 198,
                                     description=translation(30314),
                                     callb_kwargs=dict(item_id=bundle_id, page_url=current_url))

        if 'data' in programme_data:
            # A totally different data structure, found on category pages where the root folder
            # of the path is `/browse/` instead of `/categories/`.
            for rail_data in programme_data['data'].values():
                if rail_data.get('props', {}).get('dataType') == 'contentCollectionData':
                    item_data = ParseRailItem(rail_data)
                    if item_data:
                        AddMenuEntry(**item_data)

    SetSortMethods(xbmcplugin.SORT_METHOD_DATE)


def SetSortMethods(*additional_methods):
    """Set a few standard sort methods and optional additional methods"""
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,
                    xbmcplugin.SORT_METHOD_LABEL,
                    xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE]
    sort_methods.extend(additional_methods)
    handle = int(sys.argv[1])
    for method in sort_methods:
        xbmcplugin.addSortMethod(handle, method)


def SelectSynopsis(synopses: dict | str | None, is_playable: bool= True):
    if not synopses:
        return ''
    try:
        if is_playable:
            return (synopses.get('medium')
                    or synopses.get('large')
                    or synopses.get('small')
                    or synopses.get('editorial')
                    or synopses.get('programme_small')
                    or synopses.get('programmeSmall')      # Seen in bundles on iplayer's main page.
                    or synopses.get('live')
                    or '')
        else:
            return (synopses.get('programme_small')
                    or synopses.get('programmeSmall')  # Seen in bundles on iplayer's main page.
                    or synopses.get('editorial')
                    or synopses.get('medium')
                    or synopses.get('large')
                    or synopses.get('small')
                    or synopses.get('live')
                    or '')
    except AttributeError:
        # Allow for the odd event that `synopses` is a single string.
        if isinstance(synopses, str):
            return synopses
        else:
            raise


def SelectImage(images, is_playable=True):
    if not images:
        return 'DefaultFolder.png'
    if is_playable:
        return (images.get('standard')
                or images.get('default')
                or images.get('portrait')
                or images.get('promotional')
                or images.get('promotional_with_logo')
                or 'DefaultFolder.png').replace('{recipe}', '832x468')
    else:
        return (images.get('promotional_with_logo')
                or images.get('promotional')
                or images.get('portrait')
                or images.get('standard')
                or images.get('default')
                or 'DefaultFolder.png').replace('{recipe}', '832x468')


def ParseProgramme(progr_data):
    playable = progr_data.get('programme_type') == 'one-off' or progr_data.get('count') == 1

    if playable:
        children = progr_data.get('initial_children')
        if children:
            try:
                programme = ParseEpisode(children[0])
                return playable, programme
            except (KeyError, IndexError):
                pass

        programme = {
            'url': 'https://www.bbc.co.uk/iplayer/episode/' + progr_data['id'],
            'name': progr_data['title']
        }

    else:
        num_episodes = progr_data.get('count')
        if num_episodes:
            title = '[B]{}[/B] - {} episodes available'.format(progr_data['title'], num_episodes)
        else:
            title = '[B]{}[/B]'.format(progr_data['title'])

        programme = {
            'url': 'https://www.bbc.co.uk/iplayer/episodes/' + progr_data['id'],
            'name': title
        }

    labels = progr_data.get('labels') or {}     # Labels can be None or absent.
    category = labels.get('category')

    programme.update({
        'iconimage': SelectImage(progr_data.get('images'), is_playable=False),
        'description': '\n'.join(t for t in (category, SelectSynopsis(progr_data['synopses'], False)) if t),
    })
    return playable, programme


def ParseEpisode(episode_data: dict, is_standalone: bool = True):
    """Parse a dict with episode info.

    :param is_standalone: Set to True if the episode is not listed under its own programme
        or series folder. Default is True, since most callers proces episodes in other
        lisings than their programme.

    """
    title = episode_data.get('title', '')
    if isinstance(title, dict):
        title= title.get('default', '')
    subtitle = episode_data.get('subtitle')
    if isinstance(subtitle, dict):
        subtitle = subtitle.get('default')
    if subtitle:
        title = ' - '.join((title, subtitle))
    labels = episode_data.get('labels') or {}   # This field can have value None, or be absent.
    category = labels.get('category')
    description = SelectSynopsis(episode_data.get('synopses') or episode_data.get('synopsis'))
    duration = ''
    availability = ''
    version_data = episode_data.get('versions')
    if version_data:
        version = version_data[0]
        duration_data = version.get('duration', {})
        duration = duration_2_secs(duration_data.get('value') or duration_data.get('text')) or ''
        availability = version.get('availability', {}).get('remaining')
        if isinstance(availability, dict):
            availability = availability.get('text', '')
    description = '\n\n'.join(t for t in (category, description, availability) if t)

    return {
        'url': 'https://www.bbc.co.uk/iplayer/episode/' + episode_data['id'],
        'name': title,
        'iconimage': SelectImage(episode_data.get('images') or episode_data.get('image'), not is_standalone),
        'description': description,
        'aired': episode_data.get('release_date_time', '').split('T')[0],
        'total_time': str(duration)
    }


def ParseEpisodeAsProgramme(episode_data):
    """Parse Episode data, but present is as a programme folder.

    On some pages, in particular groups (A.K.A. collections), all items are of the type
    'episodes', while they link to the programme's page with all episodes and series.
    This function parses episode data as a programme.

    """
    title = episode_data.get('title', '')
    if isinstance(title, dict):
        title = title.get('default', '')
    description = SelectSynopsis(episode_data.get('synopses') or episode_data.get('synopsis'), False)
    category = episode_data.get('labels', {}).get('category')

    return {
        'url': 'https://www.bbc.co.uk/iplayer/episodes/' + episode_data['tleo_id'],
        'name': f"[B]{title}[/B]",
        'iconimage': SelectImage(episode_data.get('images') or episode_data.get('image'), is_playable=False),
        'description': '\n'.join(t for t in (category, description) if t),
    }


def ParseHeroItem(episode_data):
    try:
        item = ParseEpisode(episode_data)
        item['name'] = f"[B][COLOR orange]{item['name']}[/COLOR][/B]"
        programme_id = episode_data.get('tleo', {}).get('id')
        if programme_id and programme_id != episode_data['id']:
            ctx_mnu = [CtxMnuViewAllEpisodes(programme_id)]
            item['context_mnu'] = ctx_mnu
        return item
    except Exception as err:
        xbmc.log(f"[IPWWW-VIDEO] Failed to parse hero item: {repr(err)}")


def ParseRailItem(item_data):
    try:
        return {
            'mode': 127,            # GetGroup()
            'name': f"[B]{item_data['data']['title']}[/B]",
            'description': translation(30314),
            'callb_kwargs': {'url': item_data['data']['urn']}
        }
    except KeyError:
        # Incomplete rail data has been observed in the wild.
        return None


def ListHighlights(highlights_url):
    """Creates a list of the programmes in the highlights section.
    """

    current_url = 'https://www.bbc.co.uk/%s' % highlights_url
    html = OpenURL(current_url)

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)


def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    current_url = 'https://www.bbc.co.uk/iplayer/group/most-popular'
    html = OpenURL(current_url)

    json_data = ScrapeJSON(html)
    if json_data:
        ParseJSON(json_data, current_url)


def AddAvailableStreamItem(url):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_ad') == 'true')) and stream_ids['stream_id_ad']:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_ad'])
        strm_id = stream_ids['stream_id_ad']
    elif ((not stream_ids['stream_id_st']) or (ADDON.getSetting('search_signed') == 'true')) and stream_ids['stream_id_sl']:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_sl'])
        strm_id = stream_ids['stream_id_sl']
    else:
        streams_all = ParseStreamsHLSDASH(stream_ids['stream_id_st'])
        strm_id = stream_ids['stream_id_st']
    if streams_all[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams_all[1][0][1]
        # print subtitles_url
    else:
        subtitles_url = ''
    streams = streams_all[0]
    source = int(ADDON.getSetting('catchup_source'))
    # print "Selected source is %s"%source
    # print streams
    if source > 0:
        match = [x for x in streams if (x[0] == source)]
    else:
        match = streams
    PlayStream(match[0][2], subtitles_url,
               episode_id=stream_ids['episode_id'], stream_id=strm_id)


def GetAvailableStreams(name, url, iconimage, description, resume_time='', total_time=''):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    #print url
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['name']:
        name = stream_ids['name']
    if stream_ids['image']:
        iconimage = stream_ids['image']
    if stream_ids['description']:
        description = stream_ids['description']
    # If we found standard streams, append them to the list.
    if stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description,
                                     stream_ids['episode_id'], resume_time, total_time)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage,
                                     description, stream_ids['episode_id'], resume_time, total_time)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl'] or not stream_ids['stream_id_st']:
        AddAvailableStreamsDirectory(name + ' - (Signed)', stream_ids['stream_id_sl'], iconimage,
                                     description, stream_ids['episode_id'], resume_time, total_time)


def Search(search_entered):
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    if not search_entered:
        return False

    NEW_URL = 'https://www.bbc.co.uk/iplayer/search?q=%s' % utf8_quote_plus(search_entered)
    ScrapeEpisodes(NEW_URL)


def AddAvailableLiveStreamItemSelector(name, channelname, iconimage=None, watch_from_start=False):
    # keeping argument name and iconimage in to be compatible with AddAvailableLiveStreamsDirectory()
    return AddAvailableLiveDASHStreamItem(channelname, watch_from_start)


def AddAvailableLiveDASHStreamItem(channelname, watch_from_start=False):
    streams = ParseLiveDASHStreams(channelname)

    source = int(ADDON.getSetting('live_source'))
    if source > 0:
        match = [x for x in streams if (x[0] == source)]
        if len(match) == 0:
            match = streams
    else:
        match = streams
    if watch_from_start:
        PlayStream(match[0][2], '', '', replay_chan_id=channelname)
    else:
        PlayStream(match[0][2], '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage, watch_from_start=False):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
        watch_from_start: True if the current programme is to be played from the start.
    """
    streams = ParseLiveDASHStreams(channelname)
    suppliers = ['', 'Akamai', 'Limelight', 'Bidi','Cloudfront']
    for supplier, bitrate, url, resolution in streams:
        title = name + ' - [I][COLOR fff1f1f1]%s[/COLOR][/I]' % (suppliers[supplier])
        if watch_from_start:
            replay_chan_id = channelname
        else:
            replay_chan_id = ''
        AddMenuEntry(title, 201, iconimage,
                     callb_kwargs=dict(url=url, replay_chan_id=replay_chan_id))


def GetJsonData(url):
    html = OpenURL(url)
    return ScrapeJSON(html)


def GetJsonDataWithBBCid(url, silent= False, retry=True):
    html = OpenURL(url)
    json_data = ScrapeJSON(html)
    if not json_data:
        xbmc.log(f"[ipwww_video] [Warning] No JSON data on page '{url}'.")
        return
    identity = json_data.get('id') or json_data.get('identity')
    if identity is None or identity['signedIn']:
        return json_data

    if retry:
        if CheckLogin():
            return GetJsonDataWithBBCid(url, retry=False)
        elif silent:
            return json_data
        else:
            CreateBaseDirectory('video')
    else:
        xbmc.log('[ipwww_video] [Error] GetJsonDataWithBBCid(): still not signed in at second attempt')
        if silent:
            return json_data
        else:
            return None


def ListWatching():
    url = "https://www.bbc.co.uk/iplayer/continue-watching"
    data = GetJsonDataWithBBCid(url)
    if not data:
        return

    for watching_item in data['items']['elements']:
        episode = watching_item['episode']
        programme = watching_item['programme']
        item_data = ParseEpisode(episode)

        # Lacking a field synopses, a watching item's description is empty. Since the
        # remaining playtime is presented in the title instead of the usual episode name,
        # place the original title/sub-title in the description.
        item_data['description'] = item_data['name']
        remaining_seconds = watching_item.get('remaining')
        if remaining_seconds:
            total_seconds = int(remaining_seconds * 100 / (100 - watching_item.get('progress', 0)))
            item_data['name'] = '{} - [I]{} min left[/I]'.format(episode.get('title', ''), int(remaining_seconds / 60))
            # Resume a little bit earlier, so it's easier to recognise where you've left off.
            item_data['resume_time'] = str(max(total_seconds - remaining_seconds - 10, 0))
            item_data['total_time'] = str(total_seconds)
        else:
            item_data['name'] = '{} - [I]next episode[/I]'.format(episode.get('title', ''))

        item_data['context_mnu'] = ct_menus = []
        programme_id = episode.get('tleo_id')

        if episode.get('id') != programme_id:
            # A programme with multiple episodes; add a 'View all episodes' context menu item.
            ct_menus.append(CtxMnuViewAllEpisodes(programme['id']))

        if programme_id:
            # Add a context menu item 'Remove'
            ct_menus.append((translation(30601),
                             f'RunPlugin(plugin://plugin.video.iplayerwww?mode=301&episode_id={programme_id})'))

        CheckAutoplay(**item_data)


def CtxMnuViewAllEpisodes(programme_id: str):
    """Add a context menu item 'View all episodes'."""
    all_episodes_link = 'https://www.bbc.co.uk/iplayer/episodes/' + programme_id
    return(translation(30600),
           f'Container.Update(plugin://plugin.video.iplayerwww/?mode=128&page_url={all_episodes_link})')


def RemoveWatching(episode_id):
    """Remove an item from the 'Continue Watching' list.
    Handler for the context menu option 'Remove' on list items in 'Continue watching'.

    """
    PostJson('https://user.ibl.api.bbc.co.uk/ibl/v1/user/hides',
             {'id': episode_id})
    xbmc.executebuiltin('Container.Refresh')


def ListFavourites():
    """AKA 'Watchlist', FKA 'Added'."""
    data = GetJsonDataWithBBCid("https://www.bbc.co.uk/iplayer/watchlist")
    if not data:
        return

    for added_item in data['items']['elements']:
        programme = added_item['programme']

        ct_mnu = [(translation(30601),
                   f'RunPlugin(plugin://plugin.video.iplayerwww?mode=302&programme_id={programme["id"]})')]
        is_playable, pgm_data = ParseProgramme(programme)
        if is_playable:
            CheckAutoplay(context_mnu=ct_mnu, **pgm_data)
        else:
            url = pgm_data.pop('url')
            AddMenuEntry(mode=128, context_mnu=ct_mnu, **pgm_data, callb_kwargs=dict(page_url=url))
    SetSortMethods()


def RemoveFavourite(programme_id):
    """Remove an item from the Watchlist.
    Handler for the context menu option 'Remove' on list items in 'Watchlist'.

    Delete will never fail, even if programme_id is not on the list, or does not exist at all.
    """
    DeleteUrl('https://user.ibl.api.bbc.co.uk/ibl/v1/user/adds/' + programme_id)
    xbmc.executebuiltin('Container.Refresh')


def ListRecommendations(item_id: str = '', page_url: str = 'https://www.bbc.co.uk/iplayer'):
    data = GetJsonDataWithBBCid(page_url)
    if not data:
        return

    if item_id and item_id != 'url':
        # find the bundle and return its content from the main page:
        for bundle in data['bundles']:
            if bundle['id'] == item_id:
                for recommended_item in bundle['entities']:
                    episode = recommended_item['episode']
                    item_data = ParseEpisode(episode)
                    if not item_data:
                        continue
                    tleo_id = episode.get('tleo', {}).get('id')
                    if tleo_id and tleo_id != episode['id']:
                        item_data['context_mnu'] = [CtxMnuViewAllEpisodes(tleo_id)]
                    CheckAutoplay(**item_data)
                SetSortMethods(xbmcplugin.SORT_METHOD_DATE)
                return
    else:
        # Present the various rails of recommendations on iplayer's home page as folders in Kodi
        for bundle in data['bundles']:
            bundle_id = bundle.get('id', '')
            if bundle_id in ('recommendations', 'if-you-liked'):
                AddMenuEntry(bundle['title']['default'], 198, SelectImage(bundle.get('image')),
                             SelectSynopsis(bundle.get('synopses')), callb_kwargs=dict(item_id=bundle_id))



def PlayStream(url, subtitles_url='', episode_id=None, stream_id=None, replay_chan_id=''):
    # Check geo-block. It's quite impossible now to get here without having run into a geo-block
    # earlier, but left in just in case someone find a way.
    OpenURL(url)

    liz = xbmcgui.ListItem()
    liz.setContentLookup(False)
    liz.setMimeType('application/dash+xml')
    liz.setProperty("IsPlayable", "true")
    liz.setProperty('inputstream', 'inputstream.adaptive')
    liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    xbmc.log(f'[iPLayer www.video.PlayStream] url={url}, episodeid = {episode_id}, stream_id = {stream_id}')
    # FIXME: find a more reliable way to distinguish live from VOD
    is_live = '-cmaf' in url or '-uhd' in url
    if is_live:
        from resources.lib.proxy import run_proxy
        # live stream
        proxy_address, proxy_server = run_proxy(url)
        liz.setPath(proxy_address)
        if replay_chan_id:
            resume_point = GetLiveStartPosition(replay_chan_id)
            if resume_point is not None:
                liz.setProperties({'ResumeTime': str(resume_point),
                                   'TotalTime': '7200',
                                   'inputstream.adaptive.play_timeshift_buffer': 'true'})
    else:
        liz.setPath(url)
        if subtitles_url and ADDON.getSetting('subtitles') == 'true':
            # print "Downloading subtitles"
            subtitles_file = download_subtitles(subtitles_url)
            liz.setSubtitles([subtitles_file])
            liz.setProperties({'subtitles.translate.type': '.srt',
                               'subtitles.translate.orig_lang': 'en',
                               'subtitles.translate.file': subtitles_file})

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    ipwww_progress.monitor_progress(episode_id, stream_id)  # Blocks until the stream stops
    if is_live:
        proxy_server.stop_server(3)


def GetLiveStartPosition(chan_id):
    """Return the start position of the current programme relative to the beginning of the stream.

    :returns: The start position in seconds, or None if the start position is not available.
    """
    if not chan_id:
        return

    from datetime import datetime, timezone

    # Schedules from HD channels must be requested by their non-HD counterpart.
    if chan_id.endswith('_hd'):
        chan_id = chan_id[:-3]
    if chan_id == 'bbc_one':
        chan_id = 'bbc_one_london'

    now = datetime.now(timezone.utc)
    resp = None
    try:
        # Get schedules of the current channel to obtain the start time of the current programme.
        url = (f'https://ibl.api.bbc.co.uk/ibl/v1/channels/{chan_id}/broadcasts?per_page=2&from_date=' +
               now.strftime('%Y-%m-%dT%H:%M'))
        resp = OpenRequest('get', url)
        data = json.loads(resp)
        cur_broadcast = data['broadcasts']['elements'][0]
        # transmission_start is more accurate, but not always available.
        start = cur_broadcast.get('transmission_start') or cur_broadcast['scheduled_start']
        start_dt = strptime(start, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    except Exception as e:
        xbmcgui.Dialog().ok(translation(30400), translation(30415)) # Error msg start time not available.
        xbmc.log(f'[ipwww_video] [Error] Failed to get live resume point: {e!r}\n{resp}')
        return
    # Need to get the start of the current programme relative to the start of the stream.
    # Since a live stream has a 2 hrs timeshift window, the live edge is at 7200 seconds from the start.
    start_position = 7200 - (now - start_dt).total_seconds()
    if start_position < 0:
        if xbmcgui.Dialog().yesno(
                translation(30405),             # warning
                translation(30416),             # msg program started too long ago
                yeslabel=translation(30417),    # play from 2hrs back
                nolabel=translation(30418)):    # play live
            start_position = 0
        else:
            return
    return start_position


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description, episode_id, resume_time="", total_time=""):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print("Stream ID: %s"%stream_id)
    streams = ParseStreamsHLSDASH(stream_id)
    # print(streams)
    if streams[1]:
        # print("Setting subtitles URL")
        subtitles_url = streams[1][0][1]
        # print(subtitles_url)
    else:
        subtitles_url = ''
    suppliers = ['', 'Akamai', 'Limelight', 'Bidi','Cloudfront']
    for supplier, bitrate, url, resolution, protocol in streams[0]:
        title = name + ' - [I][COLOR ffd3d3d3]%s[/COLOR][/I]' % (suppliers[supplier])
        AddMenuEntry(title, 201, iconimage, description, resume_time=resume_time, total_time=total_time,
                     callb_kwargs=dict(url=url, subtitles_url=subtitles_url,
                                       episode_id=episode_id, stream_id=stream_id))


def ParseMediaselector(stream_id):
    streams = []
    subtitles = []
    # print("Parsing streams for PID: %s"%stream_id)
    # Open the page with the actual strem information and display the various available streams.
    fhd_enabled = ADDON.getSettingBool('live_fhd')
    media_set = 'iptv-native-hd' if fhd_enabled else 'pc'
    NEW_URL = ('https://open.live.bbc.co.uk/mediaselector/6/select/version/3.0/mediaset/%s/'
               'cvid/urn:bbc:pips:pid:%s/format/json/cors/1/proto/https') % (media_set, stream_id)
    html = OpenURL(NEW_URL)
    json_data = json.loads(html)
    video_height = 0
    if json_data:
        # print(json.dumps(json_data, sort_keys=True, indent=2))
        if 'media' in json_data:
            for media in json_data['media']:
                if 'kind' in media:
                    if media['kind'] == 'captions':
                        if 'connection' in media:
                            for connection in media['connection']:
                                protocol = connection.get('protocol', '')
                                if protocol != 'https':
                                    continue
                                href = connection.get('href', '')
                                supplier = connection.get('supplier', '')
                                subtitles.append((href, protocol, supplier))
                    elif media['kind'].startswith('video'):
                        height = int(media['height'])
                        # Pick the set with the highest resolution
                        if height < video_height:
                            continue
                        video_height = height
                        if 'connection' in media:
                            for connection in media['connection']:
                                protocol = connection.get('protocol', '')
                                if protocol != 'https':
                                    continue
                                href = connection.get('href', '')
                                supplier = connection.get('supplier', '')
                                transfer_format = connection.get('transferFormat', '')
                                streams.append((href, protocol, supplier, transfer_format))
        elif 'result' in json_data:
            # MediaSelector will probably already have returned HTTP status 403, but keep this check just to be sure.
            if json_data['result'] == 'geolocation':
                raise GeoBlockedError()
    # print("Found streams:")
    # print(streams)
    # print(subtitles)
    return streams, subtitles


def ParseStreamsHLSDASH(stream_id):
    return ParseDASHStreams(stream_id)


def ParseDASHStreams(stream_id):
    streams = []
    subtitles = []
    # print "Parsing streams for PID: %s"%stream_id
    mediaselector = ParseMediaselector(stream_id)
    # Open the page with the actual strem information and display the various available streams.
    source = int(ADDON.getSetting('catchup_source'))
    for url, protocol, supplier, transfer_format in mediaselector[0]:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'dash':
            if 'akamai' in supplier and source in [0,1]:
                tmp_sup = 1
            elif 'limelight' in supplier and source in [0,2]:
                tmp_sup = 2
            elif 'bidi' in supplier and source in [0,3]:
                tmp_sup = 3
            elif 'cloudfront' in supplier and source in [0,4]:
                tmp_sup = 4
            else:
                continue
            streams.append((tmp_sup, 1, url, '1280x720', protocol))
    source = int(ADDON.getSetting('subtitle_source'))
    for href, protocol, supplier in mediaselector[1]:
        if '$Number$' in href:
            # Found in live and red-button streams and requires `$Number$` to be replaced by
            # a DASH segment id.
            # Since DASH is handled by Inputstream Adaptive, live subtitles are not supported.
            continue
        if 'akamai' in supplier and source in [0,1]:
            tmp_sup = 1
        elif 'limelight' in supplier and source in [0,2]:
            tmp_sup = 2
        elif 'bidi' in supplier and source in [0,3]:
            tmp_sup = 3
        elif 'cloudfront' in supplier and source in [0,4]:
            tmp_sup = 4
        else:
            continue
        subtitles.append((tmp_sup, href, protocol))
    # print streams
    # print subtitles
    return streams, subtitles


def ParseLiveDASHStreams(channelname):
    streams = []
    mediaselector = ParseMediaselector(channelname)
    # print mediaselector
    for provider_url, protocol, provider_name, transfer_format in mediaselector[0]:
        if transfer_format == 'dash':
            tmp_sup = ''
            if 'akamai' in provider_name:
                tmp_sup = 1
            elif 'll' in provider_name or 'limelight' in provider_name:
                tmp_sup = 2
            elif 'bidi' in provider_name:
                tmp_sup = 3
            elif 'cloudfront' in provider_name:
                tmp_sup = 4
            else:
                continue
            streams.append((tmp_sup, 1, provider_url, '1280x720'))
    # print streams
    return streams


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    name = None
    image = None
    description = None
    stream_id_st = []
    stream_id_sl = []
    stream_id_ad = []

    json_data = ScrapeJSON(html)
    # print(json.dumps(json_data, indent=2, sort_keys=True))
    if json_data:
        if 'title' in json_data['episode']:
            name = json_data['episode']['title']
        if 'synopses' in json_data['episode']:
            synopses = json_data['episode']['synopses']
            if 'large' in synopses:
                description = synopses['large']
            elif 'medium' in synopses:
                description = synopses['medium']
            elif 'small' in synopses:
                description = synopses['small']
            elif 'editorial' in synopses:
                description = synopses['editorial']
        if 'standard' in json_data['episode']['images']:
            image = json_data['episode']['images']['standard'].replace('{recipe}','832x468')
        st = []
        ty = []
        for stream in json_data['versions']:
            if (stream['kind'] == 'original'):
                st.append(stream['id'])
                ty.append(1)
            elif (stream['kind'] == 'iplayer-version'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'technical-replacement'):
                st.append(stream['id'])
                ty.append(0)
            elif (stream['kind'] == 'editorial'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'shortened'):
                st.append(stream['id'])
                ty.append(3)
            elif (stream['kind'] == 'webcast'):
                st.append(stream['id'])
                ty.append(2)
            elif (stream['kind'] == 'simulcast'):
                st.append(stream['serviceId'])
                ty.append(0)
            elif (stream['kind'] == 'signed'):
                stream_id_sl = stream['id']
            elif (stream['kind'] == 'audio-described'):
                stream_id_ad = stream['id']
            else:
                xbmc.log("iPlayer WWW warning: New stream kind: %s" % stream['kind'])
                stream_id_st = stream['id']

            if st:
                st_st = [x for _,x in sorted(zip(ty,st))]
                stream_id_st = st_st[0]

    return {'stream_id_st': stream_id_st, 'stream_id_sl': stream_id_sl, 'stream_id_ad': stream_id_ad,
            'name': name, 'image':image, 'description': description, 'episode_id': json_data['episode'].get('id', '')}


def ScrapeJSON(html):
    json_data = None
    format = 1
    match = re.search(r'window\.mediatorDefer\=page\(document\.getElementById\(\"tviplayer\"\),(.*?)\);', html, re.DOTALL)
    if not match:
        format = 2
        match = re.search(r'window.__IPLAYER_REDUX_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if not match:
        format = 3
        match = re.search(r'window.__INITIAL_DATA__\s*=\s*(.*?);\s*</script>', html, re.DOTALL)
    if match:
        data = match.group(1)
        json_data = json.loads(data)
        if format == 1:
            if 'appStoreState' in json_data:
                json_data = json_data.get('appStoreState')
            elif 'initialState' in json_data:
                json_data = json_data.get('initialState')
        elif format == 3:
            json_data = json.loads(json_data)
        # print json.dumps(json_data, indent=2, sort_keys=True)
    return json_data


def CheckAutoplay(name, url, iconimage, description, aired=None, resume_time="", total_time="", context_mnu=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, 202, iconimage, description, aired=aired, context_mnu=context_mnu,
                     resume_time=resume_time, total_time=total_time,
                     callb_kwargs=dict(url=url))
    else:
        AddMenuEntry(name, 122, iconimage, description, aired=aired, context_mnu=context_mnu,
                     callb_kwargs=dict(name=name, url=url, iconimage=iconimage, description=description,
                                       resume_time=resume_time, total_time=total_time))


def GetSchedules(channel_list):
    """Obtain the schedule for each channel in channel_list.

    :param channel_list: A list of tuples like defined in ListLive().
        The third item of each tuple is to be the channel_id used to obtain the schedule.
    :returns: A mapping of channel_id's to schedules.

    The schedules of the regional BBC one channels only differ in the title of the
    regional news. This function renames this titel of BBC One London to a more
    generic "BBC News where you are". This way the schedules of BBC One London can be
    used for all regional BBC One channels, which will greatly reduce the number of
    HTTP request.

    Schedules for each channel is a tuple with two elements. The first is the title of the
    programme that is now on, the second is single multi-line string, with the
    time and name of each programme on a separate line. These strings are intended
    to be used in the info fields of the ListItems of live channels.

    """
    import pytz
    from concurrent import futures

    utc_tz = pytz.utc
    utc_now = datetime.datetime.now(utc_tz)
    utc_tomorrow = utc_now + timedelta(hours=20)

    try:
        # Get local timezone from Kodi's settings
        cmd_str = '{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": ["locale.timezone"], "id": 1}'
        resp_data = json.loads(xbmc.executeJSONRPC(cmd_str))
        local_tz = pytz.timezone(resp_data['result']['value'])
    except(KeyError, json.JSONDecodeError):
        # Get from tzlocal as fallback if something fails.
        from tzlocal import get_localzone
        local_tz = get_localzone()

    # Use the user's local time format without seconds. Fix weird kodi formatting for 12-hour clock.
    local_time_format = xbmc.getRegion('time').replace(':%S', '').replace('%I%I:', '%I:')

    def get_schedule(channel):
        if not channel:
            # channel has no schedule
            return '', ''
        try:
            url = ''.join(('https://ibl.api.bbc.co.uk/ibl/v1/channels/',
                          channel,
                          '/broadcasts?per_page=12&from_date=',
                          utc_now.strftime('%Y-%m-%dT%H:%M')))
            resp = OpenRequest('get', url)
            schedule_list = json.loads(resp)['broadcasts']['elements']
            text_items = []
            now_on = schedule_list[0]['episode']['title']
            for item in schedule_list:
                start_t = utc_tz.localize(strptime(item['scheduled_start'], '%Y-%m-%dT%H:%M:%S.%fZ'))
                if start_t >= utc_tomorrow:
                    break
                title = item['episode']['title']
                subtitle = item['episode'].get('subtitle', '')
                if title == 'BBC London' and 'News' in subtitle:
                    title = 'BBC News where You Are'
                text_items.append(' - '.join((start_t.astimezone(local_tz).strftime(local_time_format), title)))
            return now_on, '\n'.join(text_items)
        except Exception as e:
            xbmc.log(f"Failed to get schedule of channel {channel}: {e!r}")
            return '', ''

    schedule_channels = list({item[2] for item in channel_list})

    with futures.ThreadPoolExecutor(max_workers=16) as executor:
        res = [executor.submit(get_schedule, chan) for chan in schedule_channels]
        futures.wait(res)
    return dict(zip(schedule_channels, (r.result() for r in res)))
