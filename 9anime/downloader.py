# https://9anime.to/ajax/film/servers/yzn0 last part yzn0 can be found in the anime page url, eg. for fairy-tail nqwm
# class server and data id = 35
# li > a.active store data-id
from HTMLParser import HTMLParser
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
    # BASE_URL = 'https://9anime.to/watch/fairy-tail-final-series-dub.nqwm'
    self.base_url = base_url
    self.filename_prefix = name_prefix
    self.start_episode = start - 1
    self.get_episodes = episode_count
    self.save_dir = save_dir
    self.request = Request()

  def get_episodes_html(self):
    servers_id = re.match(r".*\.(\w+)", self.base_url).group(1)
    episode_url = '%s%s%s' % (DOMAIN_9ANIME, 'ajax/film/servers/', servers_id)
    content = self.request.get(episode_url)
    html_episodes = json.loads(content)['html']
    path = os.path.join(CUR_DIR, '%s-python.html' % self.filename_prefix)
    with open(path, 'w') as html_text:
      html_text.write(html_episodes)

  def parse_episode_html(self):
    parser = HTMLParser9anime()
    path = os.path.join(CUR_DIR, '%s-python.html' % self.filename_prefix)
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
      print "Episode %s data-id=%s" % (start + i + 1, anime_ep_ids[i])
      current_ep = start + i + 1
      content = self.request.get(sorce_info_url, {'id': anime_ep_ids[i], 'server': SERVER})
      source_html_url = json.loads(content)['target']
      print source_html_url
      path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (self.filename_prefix, current_ep))
      source_html = self.request.get(source_html_url)
      with open(path, 'w') as source_html_file:
        source_html_file.write('<!-- %s -->\n' % source_html_url)
        source_html_file.write(source_html)

      path = os.path.join(CUR_DIR, '%s-source-ep%s.html' % (self.filename_prefix, current_ep))
      with open(path, 'r') as source_html_file:
        html = source_html_file.read()
        video_info_match = re.search(r'.*eval.*\'(.*)\'\.split.*', html, re.MULTILINE)
      url_info = video_info_match.group(1).split('|')
      download_link = 'https://{subdomain}.mp4upload.com:{port}/d/{video_dir}/video.{ext}'.format(
        subdomain=url_info[49], port=url_info[136], video_dir=url_info[135], ext=url_info[133]
      )
      print download_link
      save_as = os.path.join(self.save_dir, '%s%s.mp4' % (self.filename_prefix, current_ep))
      os.system('wget --no-check-certificate %s -O %s' % (download_link, save_as)) and os.system('curl -k %s -o %s' % (download_link, save_as))

  def download(self):
    self.get_episodes_html()
    parser = self.parse_episode_html()
    self.download_videos(parser)


CUR_DIR = os.path.dirname(__file__)
DOMAIN_9ANIME = 'https://9anime.to/'
with open(os.path.join(CUR_DIR, 'config.json'), 'r') as config_fp:
  config = json.load(config_fp)
BASE_URL = config['base_url']
Downloader(
    BASE_URL, config['filename_prefix'], config['start_episode'], config['get_episodes'],
    str(config['save_in']).replace(' ', '\\ ')
).download()




# "curl 'https://9anime.to/watch/fairy-tail-final-series-dub.nqwm' \
#   -H 'authority: 9anime.to' \
#   -H 'upgrade-insecure-requests: 1' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36' \
#   -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: navigate' \
#   -H 'sec-fetch-user: ?1' \
#   -H 'sec-fetch-dest: document' \
#   -H 'referer: https://9anime.to/watch/fairy-tail-final-series.l7l6/8ooqzq' \
#   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'cookie: _ga=GA1.2.970984711.1575817783; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=252058%7CbOPngGP6fd7NE5CARzEe39j5qzHWs82x5Krc9QO2mtMHCp2lMCT6ap95nuda; __atssc=google%3B1; __cfduid=d381ab1374b85c4cac909f1e4f9fc3bba1586604103; ss=98cb75d92011964a46fb005969fc5c26; __cf_bm=08174192cd648ec14e22cca39c87a8998c853094-1586604104-1800-AfhNTLpKqtun6AG0EXD5vfyTcXrzll1g+C4ig6MuEuC8gpfuxFtdmpv1XBjOkvvtjbRnAZMNqXtl3us5vJnAALo=; _gid=GA1.2.1410357407.1586604110; session=bef1ca802d4d3c7deda64568810ae3e0042bfd7a; __atuvc=10%7C11%2C9%7C12%2C15%7C13%2C21%7C14%2C17%7C15; __atuvs=5e91a84db21a97bc004; _gat=1' \
#   --compressed"

# curl 'https://9anime.to/ajax/film/servers/nqwm' \
#   -H 'authority: 9anime.to' \
#   -H 'accept: application/json, text/javascript, */*; q=0.01' \
#   -H 'x-requested-with: XMLHttpRequest' \
#   -H 'age: 0' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'referer: https://9anime.to/watch/major-2nd-tv-2nd-season.yzn0' \
#   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'cookie: _ga=GA1.2.970984711.1575817783; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=252058%7CbOPngGP6fd7NE5CARzEe39j5qzHWs82x5Krc9QO2mtMHCp2lMCT6ap95nuda; __atssc=google%3B1; __cfduid=d381ab1374b85c4cac909f1e4f9fc3bba1586604103; ss=98cb75d92011964a46fb005969fc5c26; _gid=GA1.2.1410357407.1586604110; __cf_bm=2549f6a89300ffe5eedf9b870771166e42f89fa6-1586605906-1800-AdGX3+GVrNdfvgxI8wXsQWWJ1JAhhTfWlEzKGljG/6nR0jshpgoaFJjMAkbdldFrhPleB4zsv4PSi/bZ+4Z+WLU=; waf_token=1586607843-c280b5f2853d435d187de1d7a0dc5e34; session=581363e17649849c05977b4e6298896915774949; _gat=1; __atuvc=10%7C11%2C9%7C12%2C15%7C13%2C21%7C14%2C22%7C15; __atuvs=5e91a84db21a97bc009' \
#   --compressed

# curl 'https://9anime.to/ajax/episode/info?id=1503f01370792bd7b1c7d0a25e7d8a1433c7c0604b1a0e46b8ba9fee7ad7f354&server=35' \
#   -H 'authority: 9anime.to' \
#   -H 'accept: application/json, text/javascript, */*; q=0.01' \
#   -H 'x-requested-with: XMLHttpRequest' \
#   -H 'age: 0' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'referer: https://9anime.to/watch/major-2nd-tv-2nd-season.yzn0' \
#   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'cookie: __cfduid=d381ab1374b85c4cac909f1e4f9fc3bba1586604103; ss=98cb75d92011964a46fb005969fc5c26; __cf_bm=2549f6a89300ffe5eedf9b870771166e42f89fa6-1586605906-1800-AdGX3+GVrNdfvgxI8wXsQWWJ1JAhhTfWlEzKGljG/6nR0jshpgoaFJjMAkbdldFrhPleB4zsv4PSi/bZ+4Z+WLU=; waf_token=1586607843-c280b5f2853d435d187de1d7a0dc5e34' \
#   --compressed


# curl 'https://9anime.to/ajax/episode/info?ts=1587189600&_=780&id=e117aac630ecb9e8c5fabba7616a85545ab39420cc7f126b1fc7798e8e89a5f0&server=35' \
#   -H 'authority: 9anime.to' \
#   -H 'accept: application/json, text/javascript, */*; q=0.01' \
#   -H 'x-requested-with: XMLHttpRequest' \
#   -H 'age: 0' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'referer: https://9anime.to/watch/fairy-tail-final-series-dub.nqwm/r553nn' \
#   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'cookie: _ga=GA1.2.970984711.1575817783; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=252058%7CbOPngGP6fd7NE5CARzEe39j5qzHWs82x5Krc9QO2mtMHCp2lMCT6ap95nuda; __atssc=google%3B1; __cfduid=d381ab1374b85c4cac909f1e4f9fc3bba1586604103; ss=98cb75d92011964a46fb005969fc5c26; _gid=GA1.2.1712984876.1587180155; __atuvc=9%7C12%2C15%7C13%2C21%7C14%2C31%7C15%2C20%7C16; __atuvs=5e9a9e81b3b360c3000; __cf_bm=9a678deae8cd8f8484019f085ac130197abdc3e9-1587191427-1800-Afv2e5wXNYK1m9VBTaRj0CfmevORXrWBMg0OhVo79nA8GBIWdWc6jEr5xUrhk7CnV02hz/jkJpQclX2Q9gC6hk0YzEAYZtI26FwJx/EZrFTC; session=8efbbd2bfd8459d1d4b9273bb58723120365227d' \
#   --compressed


# curl 'https://9anime.to/ajax/film/servers/p424?episode=xwzr5z&ts=1587880800&_=732' \
#   -H 'authority: 9anime.to' \
#   -H 'accept: application/json, text/javascript, */*; q=0.01' \
#   -H 'x-requested-with: XMLHttpRequest' \
#   -H 'age: 0' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'referer: https://9anime.to/watch/inuyasha-the-final-act-dub.p424/xwzr5z' \
#   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
#   -H 'cookie: __cfduid=db9d5006f752b9b98b87685a3681d20741587884031; ss=97960df3f58e607b32a28a56230282ff; _ga=GA1.2.790964253.1587884035; _gid=GA1.2.1596020715.1587884035; _gat=1; session=e336564ef80866a857de06c4251ea206c896c745; __atuvc=1%7C18; __atuvs=5ea5300391316e19000; ppu_main_e451654ce39dadbfc0153e75d2c312ff=1; __cf_bm=b14dde2f67cea2ee4c801623edf047b321dcc23f-1587884036-1800-AfRk1zCwt8zuofPkT2wM8ka7A5+MPtWaw8x/16zM58wN2nGW1IsiSswfZM+ApRDA/tLIm6OMHmztFcOMCrCbCkExRtzkDcyD6lIMQKKJp8mJ; MarketGidStorage=%7B%220%22%3A%7B%22svspr%22%3A%22%22%2C%22svsds%22%3A2%2C%22TejndEEDj%22%3A%22OVbEiJNDZ%22%7D%2C%22C94435%22%3A%7B%22page%22%3A1%2C%22time%22%3A1587884035085%7D%2C%22C180508%22%3A%7B%22page%22%3A1%2C%22time%22%3A1587884036953%7D%7D; dom3ic8zudi28v8lr6fgphwffqoz0j6c=b9ce004b-4e3a-498f-a0cc-a5c2fb75d180%3A3%3A1; m5a4xojbcp2nx3gptmm633qal3gzmadn=hadsoks.com' \
#   --compressed