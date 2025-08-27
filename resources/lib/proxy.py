import os
import requests
import threading
from xml.etree import ElementTree as ET


import xbmc
import xbmcvfs

from resources.lib.ipwww_common import addoninfo

from http.server import HTTPServer, BaseHTTPRequestHandler

LOG_LVL = xbmc.LOGERROR

subs_adaptationset="""<AdaptationSet
  id="222"
  group="222"
  contentType="text"
  lang="en"
  mimeType="application/mp4"
  codecs="stpp.ttml.im1t"
  startWithSAP="1">
  <Role schemeIdUri="urn:mpeg:dash:role:2011" value="caption" />
  <Representation
    id="English=64000"
    bandwidth="64000">
    <SegmentTemplate
        timescale="1000"
        initialization="http://127.0.0.1:%d/caption/segment.init"
        media="t=3840/s=caption1/b=64000/$Number$.m4s" />
  </Representation>
</AdaptationSet>"""


def modify_manifest(mpd: bytes, base_url: str, server_port: int) -> bytes:
    root = ET.fromstring(mpd)
    # Register the default namespace to prevent ET adding prefixes when writing.
    fq_tag_name = root.tag
    def_namespace = fq_tag_name[1:fq_tag_name.index('}')]
    ET.register_namespace('', def_namespace)
    # Define the base url, otherwise all media requests will be made to the proxy.
    url_elem = ET.Element('BaseURL')
    url_elem.text = base_url
    root.insert(0, url_elem)
    # Insert the subtitle tag
    subs_elem = ET.fromstring(subs_adaptationset % server_port)
    root.find(f'Period', namespaces={'': def_namespace}).append(subs_elem)
    new_mpd = ET.tostring(root, encoding='utf-8', xml_declaration=False)
    return new_mpd


def read_caption_init() -> bytes:
    xbmc.log(f"[iPlayer WWW.proxy] AddonInfo path = {addoninfo['path']}", LOG_LVL)
    path = addoninfo['path']
    data_file = os.path.join(addoninfo['path'], 'resources/data/itv-caption-init')
    with open(data_file , 'rb') as f:
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
        base_url = url.rsplit('/', 1)[0]
        xbmc.log(f"[iPlayer WWW.proxy] Setting base url to '{base_url}'.")
        new_manifest = modify_manifest(resp.content, base_url, self.server.server_port)
        self.send_header('content-type', 'application/dash+xml')
        self.send_header('content_length', str(len(new_manifest)))
        self.send_header('connection', 'close')
        self.end_headers()
        self.wfile.write(new_manifest)
        # self.server.manifest_handled()
        xbmc.log('[iPlayer WWW.proxy] Finished proxying manifest', LOG_LVL)

    def _send_segment_init(self):
        data = read_caption_init()
        xbmc.log(f'[iPlayer WWW.proxy] Read caption init of {len(data)} bytes', LOG_LVL)
        self.send_response(200)
        self.send_header('content-type', 'video/mp4')
        self.send_header('content_length', str(len(data)))
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
