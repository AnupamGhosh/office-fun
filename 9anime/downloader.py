# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url, eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
from HTMLParser import HTMLParser
import logging
import httplib
import urllib
import json
import os
import re

SERVER = 35 # mp4upload

class HTMLParser9anime(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.state_mc = EpisodeInfoMachine()

  def handle_starttag(self, tag, attrs):
    self.state_mc.start_tag(tag, attrs)

  def handle_endtag(self, tag):
    self.state_mc.end_tag(tag)

  def get_ep_ids(self):
    return self.state_mc.ep_infos

  @staticmethod
  def attrs2dict(attrs):
    return {name: value for name, value in attrs}


class EpisodeInfoMachine:
  def __init__(self):
    self.ep_infos = []
    self.SERVER = str(SERVER)
    self.state_server = StateServer(self)
    self.state_li = StateLi(self)
    self.state_start = StateStart(self)
    self.state_ul = StateUl(self)

    self.state = self.state_start

  def start_tag(self, tag, attrs):
    self.state = self.state.next_state(tag, attrs)

  def end_tag(self, tag):
    self.state = self.state.next_state(tag, [], close=True)

class StateStart(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)
    div_classes = attr.get('class', '').split(' ')
    data_id = attr.get('data-id')

    if 'server' in div_classes and data_id == self.mc.SERVER:
      return self.mc.state_server
    return self

class StateServer(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)
    ul_classes = attr.get('class', '').split(' ')

    if tag == 'ul' and 'episodes' in ul_classes and 'range' in ul_classes:
      return self.mc.state_ul
    return self

class StateUl(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    if tag == 'li' and not close:
      return self.mc.state_li
    if tag == 'ul' and close:
      return self.mc.state_server
    return self

class StateLi(object):
  def __init__(self, state_mc):
    self.mc = state_mc

  def next_state(self, tag, attrs, close=False):
    attr = HTMLParser9anime.attrs2dict(attrs)

    if tag == 'li' and close:
      return self.mc.state_ul
        
    if tag == 'a' and not close:
      self.mc.ep_infos.append(attr['data-id'])
      assert int(attr['data-base']) == len(self.mc.ep_infos)
    return self

class Request(object):
  def __init__(self):
    self.header = {
      'authority': '9anime.to',
      'accept': 'application/json, text/javascript, */*; q=0.01',
      'x-requested-with': 'XMLHttpRequest',
      'age': '0',
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'referer': BASE_URL,
      'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
      'cookie': '; '.join([
          '__cfduid=db9d5006f752b9b98b87685a3681d20741587884031', 'ss=97960df3f58e607b32a28a56230282ff',
          '__cf_bm=b14dde2f67cea2ee4c801623edf047b321dcc23f-1587884036-1800-AfRk1zCwt8zuofPkT2wM8ka7A5+MPtWaw8x/16zM58wN2nGW1IsiSswfZM+ApRDA/tLIm6OMHmztFcOMCrCbCkExRtzkDcyD6lIMQKKJp8mJ',
          'waf_token=1586607843-c280b5f2853d435d187de1d7a0dc5e34'])
    }
    
  def get(self, url, params=None):
    params = params or {}
    reg_match = re.match(r"https:\/\/([^\/]*)([^?]*)(.*)", url)
    domain = reg_match.group(1)
    path = reg_match.group(2)
    temp_params = reg_match.group(3)
    if len(temp_params):
      temp_params = re.findall(r"([^=]+)=([^&]+)&", temp_params + '&')
      params.update({key: val for key, val in temp_params})
      path += '?' + urllib.urlencode(params)
    if len(params):
      path += '?' + urllib.urlencode(params)

    con = httplib.HTTPSConnection(domain)
    con.request('GET', path, '', self.header)
    res = con.getresponse()
    content = res.read()
    con.close()
    return content


class Downloader(object):

  def __init__(self, base_url, name_prefix, start, episode_count, save_dir):
    self.base_url = base_url
    self.filename_prefix = name_prefix
    self.start_episode = start - 1
    self.get_episodes = episode_count
    self.save_dir = save_dir
    self.request = Request()
    self.anime_html_filepath = os.path.join(CUR_DIR, '%s-python.html' % self.filename_prefix)

  def get_episodes_html(self):
    servers_id = re.match(r".*\.(\w+)", self.base_url).group(1)
    episode_url = '%s%s%s' % (DOMAIN_9ANIME, 'ajax/film/servers/', servers_id)
    content = self.request.get(episode_url)
    html_episodes = json.loads(content)['html']
    path = self.anime_html_filepath
    with open(path, 'w') as html_text:
      html_text.write(html_episodes)

  def parse_episode_html(self):
    parser = HTMLParser9anime()
    path = self.anime_html_filepath
    with open(path, 'r') as html_text:
      html_text = open(path, 'r')
      parser.feed(html_text.read())
    return parser

  def download_videos(self, parser):
    # get video source html page
    start = self.start_episode
    get_episodes = self.get_episodes
    anime_ep_ids = parser.get_ep_ids()[start: start + get_episodes]
    sorce_info_url = '%s%s' % (DOMAIN_9ANIME, 'ajax/episode/info')
    for i in xrange(get_episodes):
      logging.debug("Episode %s data-id=%s", start + i + 1, anime_ep_ids[i])
      current_ep = start + i + 1
      content = self.request.get(sorce_info_url, {'id': anime_ep_ids[i], 'server': SERVER})
      source_html_url = json.loads(content)['target']
      logging.debug("Source html url: %s", source_html_url)
      source_html_path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (self.filename_prefix, current_ep))
      source_html = self.request.get(source_html_url)
      with open(source_html_path, 'w') as source_html_file:
        source_html_file.write('<!-- %s -->\n' % source_html_url)
        source_html_file.write(source_html)

      html = source_html
      video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', html, re.MULTILINE)
      url_info = video_info_match.group(1).split('|')
      download_link = 'https://{subdomain}.mp4upload.com:{port}/d/{video_dir}/video.{ext}'.format(
        subdomain=url_info[49], port=url_info[136], video_dir=url_info[135], ext=url_info[133]
      )
      logging.debug("Download link: %s", download_link)
      save_as = os.path.join(self.save_dir, '%s%s.mp4' % (self.filename_prefix, current_ep))
      returncode = os.system('wget --no-check-certificate %s -O %s' % (download_link, save_as)) and os.system(
          'curl -k %s -o %s' % (download_link, save_as))
      if not returncode:
        os.remove(self.anime_html_filepath)
        os.remove(source_html_path)

  def download(self):
    self.get_episodes_html()
    parser = self.parse_episode_html()
    self.download_videos(parser)


logging.basicConfig(format='%(funcName)s:%(lineno)d %(levelname)s %(message)s', level=logging.DEBUG)
CUR_DIR = os.path.dirname(__file__)
DOMAIN_9ANIME = 'https://9anime.to/'
with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
  config = json.load(config_fp)
BASE_URL = config['base_url']
Downloader(
    BASE_URL, config['filename_prefix'], config['start_episode'], config['get_episodes'],
    str(config['save_in']).replace(' ', '\\ ')
).download()