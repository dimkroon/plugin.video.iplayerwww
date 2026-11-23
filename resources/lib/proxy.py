import os
import requests
import threading
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from urllib.parse import urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler

import xbmc

from resources.lib.ipwww_common import(
    iso_duration_2_seconds,
    seconds_2_iso_duration,
    strptime,
    addoninfo)


LOG_LVL = xbmc.LOGERROR


def log(msg, exc_info=False):
    if exc_info:
        from traceback import format_exc
        trace = '\n' + format_exc()
    else:
        trace = ''
    xbmc.log(f'[iPlayer WWW.proxy] {msg}{trace}', LOG_LVL)


class DashManifest:
    def __init__(self, manifest: bytes, manifest_url: str, proxy_port: int):
        self.proxy_port = proxy_port
        self.root = root = ET.fromstring(manifest)
        # Register the default namespace to prevent ET adding prefixes when writing.
        fq_tag_name = root.tag
        dflt_ns = fq_tag_name[1:root.tag.index('}')] if fq_tag_name.startswith('{') else ''
        if dflt_ns:
            ET.register_namespace('', dflt_ns)
            self.namespaces = {'': dflt_ns}
        else:
            self.namespaces = {}
        self.adaptation_set_ids = None
        self.group_ids = None
        self.period = period = root.find('Period', self.namespaces)
        if period is None or len(period) == 0:
            raise ValueError('Invalid DASH manifest; missing or empty Period element.')
        self.adaptation_sets = period.findall('AdaptationSet', self.namespaces)
        self.audio_sets = [aset for aset in self.adaptation_sets if
                           (aset.get('contentType') or aset.get('mimeType', '').split('/', 1)[0]) == 'audio']
        self.set_base_url(manifest_url)
        self.sanitise_timeshift_buffer()

    def set_base_url(self, manifest_url):
        """Define a fully qualified base url to avoid media segments being requested from the proxy."""
        base_url = manifest_url.split('?', 1)[0].rsplit('/', 1)[0]
        if not base_url.endswith('/'):
            base_url += '/'

        base_elem = self.root.find('BaseURL', self.namespaces)
        if base_elem is None:
            base_elem = ET.Element('BaseURL')
            base_elem.text = base_url
            self.root.insert(0, base_elem)
        else:
            base_url = urljoin(base_url, base_elem.text or '')
            base_elem.text = base_url

    def sanitise_timeshift_buffer(self):
        """Adjust the timeshift buffer to avoid a starting point earlier than the stream's start time.
        This allows special event streams to play on Kodi < 22 and does no harm on other streams.

        """
        root = self.root
        try:
            # Note: The number of decimals in the seconds can vary, causing errors when parsed with fromisoformat()
            start_t = (strptime(root.get('availabilityStartTime')[:19], '%Y-%m-%dT%H:%M:%S'))
            start_t = start_t.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, AttributeError):
            # Not a live stream
            return False
        max_timeshift = (datetime.now(timezone.utc) - start_t).total_seconds()
        max_timeshift = max_timeshift // 60 * 60
        timeshift_buf = iso_duration_2_seconds(root.get('timeShiftBufferDepth', ''))
        if timeshift_buf:
            new_ts_buf = min(max_timeshift, timeshift_buf)
        else:
            new_ts_buf = max_timeshift
        root.set('timeShiftBufferDepth', seconds_2_iso_duration(new_ts_buf))
        return True

    def _has_subtitles(self):
        """Return true if the manifest defines at least one subtitles stream."""
        subs_mimetypes = ('application/ttml+xml', 'application/mp4', 'text/xml', 'text/vtt')
        for adapt_set in self.adaptation_sets:
            if adapt_set.get('contentType') == 'text' or adapt_set.get('mimeType', '') in subs_mimetypes:
                return True
        return False

    def _new_adaptation_set_id(self):
        """Return an AdaptationSet ID not already in use in the manifest."""
        if self.adaptation_set_ids is None:
            self.adaptation_set_ids = {adaptation.get('id') for adaptation in self.adaptation_sets}
        new_id = '3'
        while new_id in self.adaptation_set_ids:
            new_id = str(int(new_id) + 1)
        self.adaptation_set_ids.add(new_id)
        return new_id

    def _new_group_id(self):
        if self.group_ids is None:
            self.group_ids = {adaptation.get('group') for adaptation in self.adaptation_sets}
        new_id = '3'
        while new_id in self.group_ids:
            new_id = str(int(new_id) + 1)
        self.group_ids.add(new_id)
        return new_id

    def add_subtitle_stream(self, subtitles_url: str) -> bool:
        log(f"Adding subtitles stream {subtitles_url}")
        if not subtitles_url:
            log("Can't add subtitles stream; no subtitles_url provided.")
            return False
        if self._has_subtitles():
            log('Subtitles are already present in the manifest.')
            return False
        # Get the timing from an audio stream
        audio_template = self.audio_sets[0].find('.//SegmentTemplate', self.namespaces)
        if audio_template is None:
            log('Missing audio SegmentTemplate in DASH manifest')
            return False
        audio_timescale = int(audio_template.get('timescale', 0))
        audio_duration = int(audio_template.get('duration', 0))
        if not (audio_timescale and audio_duration):
            log("Missing or incomplete timing in audio stream; can't add subtitle stream.")
            return False

        # noinspection bad-argument-type
        subs_adaptation_set = ET.SubElement(self.period, 'AdaptationSet', {
            'id': self._new_adaptation_set_id(),
            'group': self._new_group_id(),
            'contentType': 'text',
            'lang': 'en',
            'mimeType': 'application/mp4',
            'segmentAlignment': 'true',
            'codecs': 'stpp.ttml.im1t',
            'startWithSAP': '1',
            'impaired': 'true',
            'forced': addoninfo['addon'].getSetting('subtitles'),
            'default': 'false'
        })
        ET.SubElement(subs_adaptation_set, 'Role', {
            'schemeIdUri': 'urn:mpeg:dash:role:2011',
            'value': 'caption',
        })
        subtitle_representation = ET.SubElement(subs_adaptation_set, 'Representation', {
            'id': 's=caption1',
            'bandwidth': '64000',
        })
        ET.SubElement(subtitle_representation, 'SegmentTemplate', {
            'timescale': '1000',
            'duration': str(audio_duration * 1000 // audio_timescale),
            'initialization': f"http://127.0.0.1:{self.proxy_port}/{addoninfo['id']}/caption/segment.init",
            'media': subtitles_url
        })
        return True

    def to_string(self):
        return ET.tostring(self.root, encoding='utf-8', xml_declaration=False)


def read_captions_init() -> bytes:
    data_file = os.path.join(addoninfo['path'], 'resources/data/captions-segment-init')
    with open(data_file, 'rb') as f:
        return f.read()


class ProxyServer(HTTPServer):
    def __init__(self, server_address, req_handler, mpd_url, subtitles_url=None, bind_and_activate=True):
        super().__init__(server_address, req_handler, bind_and_activate)
        self.mpd_url = mpd_url
        self.subs_url = subtitles_url or ''
        self._serv_thread = None

    def start_server(self):
        self._serv_thread = threading.Thread(target=self._serve_forever_, daemon=True)
        self._serv_thread.start()
        log('Proxy server started')

    def _serve_forever_(self):
        super().serve_forever()
        log("Closing proxy server.")
        self.server_close()

    def stop_server(self, timeout=None):
        log('Stopping proxy server')
        self.shutdown()
        if self._serv_thread:
            if self._serv_thread.is_alive():
                self._serv_thread.join(timeout)
                log('Proxy server has stopped')
            else:
                log('Server has already stopped')
        else:
            log('Proxy server has not started yet')

    def manifest_handled(self):
        """Called by a request handler when a manifest has been handled.

        The manifest is requested only once. If the server doesn't have to serve
        subtitle init segments, it can now be closed. With segmented subtitles, the
        server has to remain open, as the initialisation segment could be requested
        each time the subtitles are disabled/enabled in Kodi.

        """
        if not self.subs_url:
            log("Manifest handled; the server will shut down once the request has been completed.")
            # noinspection attribute-outside-init
            self._BaseServer__shutdown_request = True


class ProxyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server: ProxyServer):
        self.server: ProxyServer = server
        super().__init__(request, client_address, server)
        self.protocol_version = 'HTTP/1.1'

    def do_GET(self):
        # path, qs = self.path.rsplit('?', 1)  # Path with parameters received from request e.g. "/manifest?id=234324"
        log(f'HTTP GET Request received to {self.path}')
        addon_id = addoninfo['id']
        # noinspection broad-exception
        try:
            if self.path == f'/{addon_id}/manifest.mpd':
                self._send_manifest()
            elif self.path == f'/{addon_id}/caption/segment.init':
                self._send_segment_init()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception:
            log(f"Error handling request '{self.path}:", exc_info=True)
            self.send_response(500)
            self.end_headers()

    def _send_manifest(self):
        url = self.server.mpd_url
        log('Upstream manifest url = {}'.format(url))
        resp = requests.get(url)
        status_code = resp.status_code

        if status_code != 200:
            self.send_response(status_code)
            self.end_headers()
            return

        log('Received manifest from upstream server')
        # noinspection broad-exception
        try:
            manifest = DashManifest(resp.content, resp.url, self.server.server_port)
            manifest.add_subtitle_stream(self.server.subs_url)
            new_manifest = manifest.to_string()
        except Exception:
            log("Unexpected error modifying manifest:", exc_info=True)
            # Redirect the player to the upstream manifest.
            self.send_response(302)
            self.send_header('location', resp.url)
            self.end_headers()
            return

        self.send_response(status_code)
        self.send_header('content-type', 'application/dash+xml')
        self.send_header('content-length', str(len(new_manifest)))
        self.send_header('connection', 'close')
        self.end_headers()
        self.wfile.write(new_manifest)
        self.server.manifest_handled()
        log('Finished proxying manifest')

    def _send_segment_init(self):
        data = read_captions_init()
        log(f'Read caption init of {len(data)} bytes')
        self.send_response(200)
        self.send_header('content-type', 'video/mp4')
        self.send_header('content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        log('Finished sending caption init')


def run_proxy(mpd_url, subtitles_url):
    proxy = ProxyServer(('127.0.0.1', 0), ProxyRequestHandler, mpd_url, subtitles_url)
    proxy_address = f'http://127.0.0.1:{proxy.server_port}/{addoninfo["id"]}/manifest.mpd'
    proxy.start_server()
    return proxy_address, proxy
