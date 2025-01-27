# -*- coding: utf-8 -*-

from __future__ import division

import os
import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from resources.lib import ipwww_common as Common
    from resources.lib import ipwww_video as Video
    from resources.lib import ipwww_radio as Radio
except ImportError as error:
    d = xbmcgui.Dialog()
    d.ok(str(error), xbmcaddon.Addon(Common.addonid).getLocalizedString(30413))
    raise


plugin_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')
params = dict(parse_qsl(sys.argv[2].lstrip('?')))
mode = int(params.pop('mode', 0))

try:
    # These are the modes which tell the plugin where to go.
    if not mode:
        Common.CreateBaseDirectory(**params)

    elif mode == 1:
        Common.KidsMode()

    # Modes 101-119 will create a main directory menu entry
    elif mode == 101:
        Video.ListLive(**params)

    elif mode == 102:
        Video.ListAtoZ(**params)

    elif mode == 103:
        Video.ListCategories(**params)

    elif mode == 104:
        from resources.lib.ipwww_search import list_search_terms

        mode = 130 if params.get('content_type') == 'video' else 140
        list_search_terms(mode=mode, **params)

    elif mode == 105:
        Video.ListMostPopular()

    elif mode == 106:
        Video.ListHighlights(**params)

    elif mode == 107:
        Video.ListWatching()

    elif mode == 108:
        Video.ListFavourites()

    elif mode == 109:
        Video.ListChannelHighlights()

    elif mode == 112:
        Radio.ListAtoZ()

    elif mode == 113:
        Radio.ListLive()

    elif mode == 114:
        Radio.ListGenres()

    elif mode == 116:
        Radio.ListMostPopular()

    elif mode == 117:
        Radio.ListListenList()

    elif mode == 199:
        Radio.ListFollowing()

    elif mode == 118:
        Video.RedButtonDialog()

    elif mode == 119:
        Common.SignOutBBCiD()

    elif mode == 120:
        Video.ListChannelAtoZ()

        # Modes 121-199 will create a sub directory menu entry
    elif mode == 121:
        Video.GetEpisodes(**params)

    elif mode == 122:
        Video.GetAvailableStreams(**params)

    elif mode == 123:
        Video.AddAvailableLiveStreamsDirectory(**params)

    elif mode == 124:
        Video.GetAtoZPage(**params)

    elif mode == 125:
        Video.ListCategoryFilters(**params)

    elif mode == 126:
        Video.GetFilteredCategory(**params)

    elif mode == 127:
        Video.GetGroup(**params)

    elif mode == 128:
        Video.ScrapeEpisodes(**params)

    elif mode == 129:
        Video.AddAvailableRedButtonDirectory(**params)

    elif mode == 130:
        from resources.lib.ipwww_search import do_search
        do_search(**params)

    elif mode == 131:
        Radio.GetEpisodes(**params)

    elif mode == 132:
        Radio.GetAvailableStreams(**params)

    elif mode == 133:
        Radio.AddAvailableLiveStreamsDirectory(**params)

    elif mode == 134:
        Video.ScrapeAtoZEpisodes(**params)

    elif mode == 136:
        Radio.GetPage(**params)

    elif mode == 137:
        Radio.GetCategoryPage(**params)

    elif mode == 138:
        Radio.GetAtoZPage(**params)

    elif mode == 139:
        Video.ScrapeEpisodes(**params)

    elif mode == 140:
        from resources.lib.ipwww_search import do_search
        do_search(**params)

    elif mode == 190:
        from resources.lib.ipwww_search import new_search
        new_search(**params)

    # Modes 201-299 will create a playable menu entry, not a directory
    elif mode == 201:
        Video.PlayStream(**params)

    elif mode == 202:
        Video.AddAvailableStreamItem(**params)

    elif mode == 203:
        Video.AddAvailableLiveStreamItemSelector(**params)

    elif mode == 204:
        Video.AddAvailableRedButtonItem(**params)

    elif mode == 205:
        Video.AddAvailableUHDTrialItem(**params)

    elif mode == 211:
        Radio.PlayStream(**params)

    elif mode == 212:
        Radio.AddAvailableStreamItem(**params)

    elif mode == 213:
        Radio.AddAvailableLiveStreamItem(**params)

    elif mode == 197:
        Video.ListUHDTrial()

    elif mode == 198:
        Video.ListRecommendations(**params)

    # Modes 301 - 399: Context menu handlers
    elif mode == 301:
        Video.RemoveWatching(**params)

    elif mode == 302:
        Video.RemoveFavourite(**params)

    # Reserved mode 303 for AddFavourite

    elif mode == 304:
        from resources.lib.ipwww_search import context_menu
        context_menu(**params)

    # Modes 401 - 499: Called as script, e.g. IPTV manager requesting channels
    elif mode == 401:
        from resources.lib.ipwww_iptv import channels
        channels(params['port'])

    elif mode == 402:
        from resources.lib.ipwww_iptv import epg
        epg(params['port'])

    elif mode == 305:
        from resources.lib.ipwww_search import edit_search_term
        edit_search_term(**params)


except Exception as err:
    import traceback
    xbmcgui.Dialog().ok(Common.translation(30400), str(err))
    xbmc.log('[ipwww.default][error] ' + traceback.format_exc())
    sys.exit(1)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
