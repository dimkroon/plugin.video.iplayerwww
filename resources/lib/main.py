# -*- coding: utf-8 -*-

import sys
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from resources.lib import ipwww_common as Common
    from resources.lib import ipwww_video as Video
except ImportError as error:
    d = xbmcgui.Dialog()
    d.ok(str(error), xbmcaddon.Addon(Common.addonid).getLocalizedString(30413))
    raise


def run():
    plugin_handle = int(sys.argv[1])
    params = dict(parse_qsl(sys.argv[2].lstrip('?')))
    mode = int(params.pop('mode', 0))
    results = None

    try:
        # These are the modes which tell the plugin where to go.
        if not mode:
            results = Common.CreateBaseDirectory(**params)

        elif mode == 1:
            results = Common.KidsMode()

        # Modes 101-119 will create a main directory menu entry
        elif mode == 101:
            results = Video.ListLive()

        elif mode == 102:
            results = Video.ListAtoZ()

        elif mode == 103:
            results = Video.ListCategories()

        elif mode == 104:
            from resources.lib.ipwww_search import list_search_terms
            results = list_search_terms(**params)

        elif mode == 105:
            results = Video.ListMostPopular()

        elif mode == 106:
            results = Video.ListHighlights(**params)

        elif mode == 107:
            results = Video.ListWatching()

        elif mode == 108:
            results = Video.ListFavourites()

        elif mode == 109:
            results = Video.ListChannels()

        elif mode == 112:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListAtoZ()

        elif mode == 113:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListLive()

        elif mode == 114:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListGenres()

        elif mode == 116:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListMostPopular()

        elif mode == 117:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListListenList()

        elif mode == 199:
            from resources.lib import ipwww_radio as Radio
            results = Radio.ListFollowing()

        elif mode == 119:
            results = Common.SignOutBBCiD()

        elif mode == 120:
            results = Video.GetChannelPage(**params)

            # Modes 121-199 will create a sub directory menu entry
        elif mode == 121:
            results = Video.GetEpisodes(**params)

        elif mode == 122:
            results = Video.GetAvailableStreams(**params)

        elif mode == 123:
            results = Video.AddAvailableLiveStreamsDirectory(**params)

        elif mode == 124:
            results = Video.GetAtoZPage(**params)

        elif mode == 125:
            results = Video.ListCategoryFilters(**params)

        elif mode == 126:
            results = Video.GetFilteredCategory(**params)

        elif mode == 127:
            results = Video.GetGroup(**params)

        elif mode == 128:
            results = Video.ScrapeEpisodes(**params)

        elif mode == 130:
            from resources.lib.ipwww_search import do_search
            results = do_search(**params)

        elif mode == 131:
            from resources.lib import ipwww_radio as Radio
            results = Radio.GetEpisodes(**params)

        elif mode == 132:
            from resources.lib import ipwww_radio as Radio
            results = Radio.GetAvailableStreams(**params)

        elif mode == 133:
            from resources.lib import ipwww_radio as Radio
            results = Radio.AddAvailableLiveStreamsDirectory(**params)

        elif mode == 136:
            from resources.lib import ipwww_radio as Radio
            results = Radio.GetPage(**params)

        elif mode == 137:
            from resources.lib import ipwww_radio as Radio
            results = Radio.GetCategoryPage(**params)

        elif mode == 138:
            from resources.lib import ipwww_radio as Radio
            results = Radio.GetAtoZPage(**params)

        elif mode == 190:
            from resources.lib.ipwww_search import new_search
            results = new_search(**params)

        # Modes 201-299 will create a playable menu entry, not a directory
        elif mode == 201:
            Video.PlayStream(**params)

        elif mode == 202:
            Video.AddAvailableStreamItem(**params)

        elif mode == 203:
            Video.AddAvailableLiveStreamItemSelector(**params)

        elif mode == 205:
            Video.AddAvailableUHDTrialItem(**params)

        elif mode == 211:
            from resources.lib import ipwww_radio as Radio
            Radio.PlayStream(**params)

        elif mode == 212:
            from resources.lib import ipwww_radio as Radio
            Radio.AddAvailableStreamItem(**params)

        elif mode == 213:
            from resources.lib import ipwww_radio as Radio
            Radio.AddAvailableLiveStreamItem(**params)

        elif mode == 197:
            results = Video.ListUHDTrial()

        elif mode == 198:
            results = Video.ListRecommendations(**params)

        # Modes 301 - 399: Context menu handlers
        elif mode == 301:
            Video.RemoveWatching(**params)

        elif mode == 302:
            Video.RemoveFavourite(**params)

        elif mode == 303:
            xbmc.log(f'[iPlayer WWW] calling handler of mode 303', xbmc.LOGWARNING)
            Video.AddFavourite(**params)

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

        if results:
            Common.PushMenuItems(results)

    except Exception as err:
        import traceback
        xbmcgui.Dialog().ok(Common.translation(30400), str(err))
        xbmc.log('[ipwww.default][error] ' + traceback.format_exc())
        sys.exit(1)

    xbmcplugin.endOfDirectory(plugin_handle)
