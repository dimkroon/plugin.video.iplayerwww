import os
import requests
import threading
from copy import deepcopy
from typing import Optional, Tuple
from xml.etree import ElementTree as ET
from urllib.parse import urljoin, urlsplit, urlunsplit


import xbmc
import xbmcvfs

from resources.lib.ipwww_common import addoninfo

from http.server import HTTPServer, BaseHTTPRequestHandler

LOG_LVL = xbmc.LOGERROR


def _qualified_name(namespace: str, name: str) -> str:
    return f'{{{namespace}}}{name}' if namespace else name


def _directory_url(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path
    if not path.endswith('/'):
        path += '/'
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _has_segment_schedule(attributes: dict, timeline) -> bool:
    try:
        if int(attributes.get('timescale', '1')) <= 0:
            return False
    except ValueError:
        return False

    if timeline is not None:
        for segment in timeline:
            if segment.tag.rsplit('}', 1)[-1] != 'S':
                continue
            try:
                if int(segment.get('d', '0')) > 0:
                    return True
            except ValueError:
                continue
        return False

    try:
        return int(attributes.get('duration', '0')) > 0
    except ValueError:
        return False


def _get_segment_schedule(root, period, namespace) -> Optional[Tuple[dict, Optional[ET.Element]]]:
    segment_template = _qualified_name(namespace, 'SegmentTemplate')
    adaptation_set = _qualified_name(namespace, 'AdaptationSet')
    representation = _qualified_name(namespace, 'Representation')
    timeline_tag = _qualified_name(namespace, 'SegmentTimeline')
    root_template = root.find(segment_template)
    period_template = period.find(segment_template)

    for adaptation in period.findall(adaptation_set):
        content_type = adaptation.get('contentType') or adaptation.get('mimeType', '').split('/', 1)[0]
        if content_type not in ('audio', 'video'):
            continue

        representations = adaptation.findall(representation) or [None]
        for rep in representations:
            templates = [root_template, period_template, adaptation.find(segment_template)]
            if rep is not None:
                templates.append(rep.find(segment_template))
            attributes = {}
            timeline = None
            for template in templates:
                if template is None:
                    continue
                attributes.update(template.attrib)
                found_timeline = template.find(timeline_tag)
                if found_timeline is not None:
                    timeline = found_timeline
            if _has_segment_schedule(attributes, timeline):
                return attributes, timeline
    return None


def modify_manifest(mpd: bytes, base_url: str, server_port: int) -> bytes:
    root = ET.fromstring(mpd)
    # Register the default namespace to prevent ET adding prefixes when writing.
    fq_tag_name = root.tag
    def_namespace = fq_tag_name[1:root.tag.index('}')] if fq_tag_name.startswith('{') else ''
    ET.register_namespace('', def_namespace)

    def qname(name):
        return _qualified_name(def_namespace, name)

    upstream_base = _directory_url(base_url)
    base_urls = root.findall(qname('BaseURL'))
    if not base_urls:
        base_elem = ET.Element(qname('BaseURL'))
        base_elem.text = upstream_base
        root.insert(0, base_elem)
    else:
        for base_elem in base_urls:
            relative_base = (base_elem.text or '').strip()
            resolved_base = urljoin(upstream_base, relative_base)
            base_elem.text = _directory_url(resolved_base)

    period = root.find(qname('Period'))
    if period is not None:
        schedule = _get_segment_schedule(root, period, def_namespace)
        if schedule is not None:
            attributes, timeline = schedule
            used_ids = {adaptation.get('id') for adaptation in period.findall(qname('AdaptationSet'))}
            adaptation_id = '3'
            while adaptation_id in used_ids:
                adaptation_id = str(int(adaptation_id) + 1)

            subtitle_adaptation = ET.SubElement(period, qname('AdaptationSet'), {
                'id': adaptation_id,
                'group': '3',
                'contentType': 'text',
                'lang': 'en',
                'mimeType': 'application/mp4',
                'segmentAlignment': 'true',
                'codecs': 'stpp.ttml.im1t',
                'startWithSAP': '1',
            })
            ET.SubElement(subtitle_adaptation, qname('Role'), {
                'schemeIdUri': 'urn:mpeg:dash:role:2011',
                'value': 'caption',
            })
            subtitle_representation = ET.SubElement(subtitle_adaptation, qname('Representation'), {
                'id': 's=caption1',
                'bandwidth': '64000',
            })

            attributes = dict(attributes)
            attributes['initialization'] = f'http://127.0.0.1:{server_port}/caption/segment.init'
            attributes['media'] = 't=3840/s=caption1/b=64000/$Number$.m4s'
            subtitle_template = ET.SubElement(subtitle_representation, qname('SegmentTemplate'), attributes)
            if timeline is not None:
                subtitle_template.append(deepcopy(timeline))

    return ET.tostring(root, encoding='utf-8', xml_declaration=False)


def read_caption_init() -> bytes:
    path = addoninfo['path']
    xbmc.log(f"[iPlayer WWW.proxy] AddonInfo path = {path}", LOG_LVL)
    data_file = os.path.join(path, 'resources/data/ip-caption.init')
    with open(data_file, 'rb') as f:
        return f.read()


class ProxyRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.protocol_version = 'HTTP/1.1'

    def do_GET(self):
        # path, qs = self.path.rsplit('?', 1)  # Path with parameters received from request e.g. "/manifest?id=234324"
        xbmc.log(f'[iPlayer WWW.proxy] HTTP GET Request received to {self.path}', LOG_LVL)
        try:
            if self.path == '/manifest.mpd':
                self._send_manifest()
            elif self.path == '/caption/segment.init':
                self._send_segment_init()
            else:
                self.send_response(404)
                self.end_headers()
        except:
            import traceback
            xbmc.log(f"[iPlayer WWW.proxy] Error handling request '{self.path}:\n{traceback.format_exc()}")
            self.send_response(500)
            self.end_headers()

    def _send_manifest(self):
        url = self.server.mpd_url
        xbmc.log('[iPlayer WWW.proxy] Upstream manifest url = {}'.format(url), LOG_LVL)
        resp = requests.get(url)
        status_code = resp.status_code
        self.send_response(status_code)
        if status_code != 200:
            self.end_headers()
            return None
        xbmc.log('[iPlayer WWW.proxy] Received manifest from upstream server')
        base_url = urljoin(resp.url or url, '.')
        xbmc.log(f"[iPlayer WWW.proxy] Setting base url to '{base_url}'.")
        new_manifest = modify_manifest(resp.content, base_url, self.server.server_port)
        self.send_header('Content-Type', 'application/dash+xml')
        self.send_header('Content-Length', str(len(new_manifest)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(new_manifest)
        # self.server.manifest_handled()
        xbmc.log('[iPlayer WWW.proxy] Finished proxying manifest', LOG_LVL)

    def _send_segment_init(self):
        data = read_caption_init()
        xbmc.log(f'[iPlayer WWW.proxy] Read caption init of {len(data)} bytes', LOG_LVL)
        self.send_response(200)
        self.send_header('Content-Type', 'video/mp4')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        # self.server.manifest_handled()
        xbmc.log('[iPlayer WWW.proxy] Finished sending caption init', LOG_LVL)


class ProxyServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, mpd_url, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.mpd_url = mpd_url

    def start_server(self):
        self._serv_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._serv_thread.start()
        xbmc.log('[iPlayer WWW.proxy] Proxy server started', LOG_LVL)

    def stop_server(self, timeout=None):
        xbmc.log('[iPlayer WWW.proxy] Stopping proxy server', LOG_LVL)
        self.shutdown()
        if self._serv_thread:
            if self._serv_thread.is_alive():
                xbmc.log('[iPlayer WWW.proxy] Waiting for all Server threads to end', LOG_LVL)
                self._serv_thread.join(timeout)
                xbmc.log('[iPlayer WWW.proxy] Proxy server has stopped', LOG_LVL)
            else:
                xbmc.log('[iPlayer WWW.proxy] Server has already stopped', LOG_LVL)
        else:
            xbmc.log('[iPlayer WWW.proxy] Proxy server has not started yet', LOG_LVL)

    def manifest_handled(self):
        """Called by a request handler when a manifest has been handled.

        Since only one manifest is requested at the start of the stream,
        the server can now shut down after the request is handled.

        """
        self._BaseServer__shutdown_request = True


def run_proxy(mpd_url):
    proxy = ProxyServer(('127.0.0.1', 0), ProxyRequestHandler, mpd_url)
    proxy_address = ''.join(('http://127.0.0.1:', str(proxy.server_port), '/manifest.mpd'))
    proxy.start_server()
    return proxy_address, proxy
