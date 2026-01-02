
import os
import json
import time
from datetime import datetime

import xbmc
import xbmcplugin

from resources.lib.ipwww_common import (
    translation,
    DIR_USERDATA,
    AddMenuEntry,
    icondir)
from resources.lib import ipwww_video


class SearchHistory:
    """
    A class providing an easy interface to saved search terms.

    :param content_type: The media type of the search terms, either `video`, for iplayer
        keywords, or `audio` for sounds.
    """

    def __init__(self, content_type: str):
        self.full_path = os.path.join(DIR_USERDATA, 'search_terms.json')
        if content_type not in ('video', 'audio'):
            raise ValueError(f"Invalid content_type '{content_type}' for SearchHistory. "
                             "Only 'video' and 'audio' are allowed.")
        self.content_type = content_type
        file_content = self._read_file()
        self._keywords = file_content.setdefault(content_type, {})

    def _read_file(self):
        try:
            with open(self.full_path, 'r', encoding='utf8') as f:
                data = json.load(f)
                return data
        except (OSError, KeyError, TypeError):
            return {}

    def _save_file(self):
        _file_content = self._read_file()
        _file_content[self.content_type] = self._keywords
        # dumps first, so as not to overwrite existing data on json errors.
        new_data = json.dumps(_file_content)
        with open(self.full_path, 'w', encoding='utf8') as f:
            f.write(new_data)

    def append(self, keyword: str):
        """Add `keyword` to the saved search terms.

        :param keyword: The search term to save.

        """
        xbmc.log(f"[ipwww_search] Adding new search term '{keyword}' to {self.content_type} list")
        if not keyword or keyword in self._keywords.keys():
            return
        now = time.time()
        self._keywords[keyword] = {'created': now, 'last_used': now}
        self._save_file()

    def update_last_used(self, keyword):
        try:
            self._keywords[keyword]['last_used'] = time.time()
        except KeyError:
            raise ValueError(f"Keyword '{keyword}' is not in present in {self.content_type} search history.") from None
        self._save_file()

    def remove(self, keyword: str):
        """Remove `term` from the saved search terms for the specified media type.
        Fails silently when `term` does not exist in the search history.

        :param keyword: The search term to remove.

        """
        xbmc.log(f"[ipwww_search] Removing search term '{keyword}' from the {self.content_type} list")
        if keyword not in self._keywords.keys():
            return
        del self._keywords[keyword]
        self._save_file()

    def clear(self):
        """Remove al search terms."""
        xbmc.log(f"[ipwww_search] Clear search history of {self.content_type}.")
        self._keywords.clear()
        self._save_file()

    def replace(self, existing: str, new: str):
        """Replace an existing keyword with a new one.

        :param existing: The existing keyword to replace.
        :param new: The new keyword that will replace the existing.
        :raises: ValueError if `existing` is not present in the search history
        """
        xbmc.log(f"[ipwww_search] Replacing search term '{existing}' for {new} in the {self.content_type} history")
        try:
            date_info = self._keywords.pop(existing)
        except KeyError:
            raise ValueError(f"Keyword '{existing}' is not in present in {self.content_type} search history.") from None
        self._keywords[new] = date_info
        self._save_file()

    def __bool__(self):
        return bool(self._keywords)

    def __iter__(self):
        try:
            return iter(sorted(self._keywords.items(), key=lambda a: a[1]['last_used'], reverse=True))
        except AttributeError:
            xbmc.log(f"[ipwww_search] Search history file has an invalid format. "
                     f"Items in section '{self.content_type}' will be cleared.")
            self._keywords = {}
            self._save_file()
            raise RuntimeError("Invalid search history file.")


def open_keyboard(content_type):
    heading = ' - '.join((translation(30304), 'iPlayer' if content_type == 'video' else 'Sounds'))
    keyboard = xbmc.Keyboard('', heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return ''


def list_search_terms(content_type: str, mode: int):
    """Create a listing of saved search terms, starting with an item that enables users
    to enter a new search term using the on-screen keyboard.

    :param content_type: The media type of the search terms, either `video`, for iplayer
        searches, or `audio` for sounds.
    :param mode: The mode to define the callback that is to perform the actual search.
    """
    icon = icondir + 'search.png'
    search_history = SearchHistory(content_type)
    txt_remove = translation(30601)
    txt_edit = translation(30604)
    txt_clear = translation(30605)

    AddMenuEntry('New Search', url=content_type, mode=190, iconimage=icon, item_position='top')
    for keyword, date_info in search_history:
        ctx_mnu = [(txt_remove,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=remove&keyword={keyword})'),
                   (txt_edit,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=edit&keyword={keyword})'),
                   (txt_clear,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=clear)')
                   ]
        date_created = datetime.fromtimestamp(date_info['created']).strftime('%Y-%m-%d')
        AddMenuEntry(keyword, keyword, mode, icon, aired=date_created, context_mnu=ctx_mnu)
    ipwww_video.SetSortMethods(xbmcplugin.SORT_METHOD_DATE)


def new_search(content_type, mode):
    keyword = open_keyboard(content_type)
    if keyword:
        SearchHistory(content_type).append(keyword)
        xbmc.executebuiltin(f'Container.Update(plugin://plugin.video.iplayerwww?mode={mode}&url={keyword})')


def do_search(content_type, keyword):
    SearchHistory(content_type).update_last_used(keyword)
    if content_type == 'video':
        ipwww_video.Search(keyword)
    elif content_type == 'audio':
        from resources.lib import ipwww_radio
        ipwww_radio.Search(keyword)


def context_menu(content_type: str, action: str, keyword: str = None):
    """Handle all search related context menu items."""
    search_history = SearchHistory(content_type)

    if action == 'remove':
        search_history.remove(keyword)
    elif action == 'clear':
        search_history.clear()
    elif action == 'edit':
        heading = ' - '.join((translation(30604), keyword))
        keyboard = xbmc.Keyboard(keyword, heading)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return

        new_term = keyboard.getText()
        if new_term == '':
            search_history.remove(keyword)
        else:
            search_history.replace(keyword, new_term)
    else:
        xbmc.log(f"[ipwww_search] Invalid context menu action '{action}'.")
    xbmc.executebuiltin('Container.Refresh')
