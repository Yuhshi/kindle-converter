# coding=utf8
import lxml.html
import lxml.etree
from PIL import Image, ImageDraw, ImageFont
import textwrap
import urllib2
import sys
import yaml
import os
import os.path
import shutil
import time

DEFAULT_PAGE_HTML = """\
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body></body>
</html>
"""

DEFAULT_TOC_NCX = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<docTitle><text></text></docTitle>
<navMap></navMap>
</ncx>
"""
DEFAULT_NAV_POINT = """\
<navPoint>
    <navLabel><text></text></navLabel><content/>
</navPoint>
"""

DEFAULT_OPF = """\
<?xml version="1.0" encoding="utf-8"?>
<package unique-identifier="uid">
  <metadata>
    <dc-metadata xmlns:dc="http://purl.org/metadata/dublin_core"
    xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
      <dc:Title></dc:Title>
      <dc:Language>en-us</dc:Language>
      <dc:Creator></dc:Creator>
      <dc:Description></dc:Description>
      <dc:Date>01/12/2015</dc:Date>
    </dc-metadata>
    <x-metadata>
         <output encoding="utf-8" content-type="text/x-oeb1-document"></output>
	  <EmbeddedCover>cover.jpg</EmbeddedCover>
    </x-metadata>
  </metadata>
  <manifest>
    <item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx"></item>
  </manifest>
  <spine toc="toc">
  </spine>
  <tours></tours>
  <guide>
  </guide>
</package>
"""

def file_put_contents(str, filename, option='w'):
    f = open(filename, option)
    f.write(str)
    f.close()

def get_filename_from_url(url, base_url=False):
    if base_url :
        url = url.replace(base_url, '')
    url = url.split('?')[0]
    return url

def mkdir_if_not_exist(path):
    dir = os.path.dirname(path)
    if os.path.exists(dir): return None
    os.makedirs(dir)

def create_navPoint(id, order, text, src):
    navPoint = lxml.etree.fromstring(DEFAULT_NAV_POINT)
    navPoint.set('id', id)
    navPoint.set('playOrder', str(order))
    navPoint.xpath('//text')[0].text = text
    navPoint.xpath('//content')[0].set('src', src)
    return navPoint


# 設定ファイルの読み込み
if (len(sys.argv) < 2):
    print 'Usage: #python %s /path/to/config.yaml' % sys.argv[0]
    quit()
config = yaml.load(open(sys.argv[1]).read())

# convert メソッドを準備する
try:
    exec(config['convert'])
    if (not callable(convert)): raise Error()
except Exception as e:
    print "convert メソッドの読み込みでエラーが発生しました。処理を打ち切ります。"
    raise



# CSS 取得
css_list = [];
if (not os.path.exists('style')):
    os.mkdir('style')
for url in config['css']:
    filename = 'style/' + get_filename_from_url(url, config['base'])
    if (os.path.exists(filename)): continue
    file_put_contents(urllib2.urlopen(url).read(), filename)

# 元の HTML を保存する (すでにあればそれ以上取得しない)
original_list = [];
if (not os.path.exists('original')):
    os.mkdir('original')
for url in config['html']:
    filename = 'original/' + get_filename_from_url(url, config['base'])
    original_list.append(filename)
    if (os.path.exists(filename)): continue
    mkdir_if_not_exist(filename)
    file_put_contents(urllib2.urlopen(url).read(), filename)
    time.sleep(1)

# HTML を整形して保存する
html_list = [];
if (not os.path.exists('html')):
    os.mkdir('html')
for url in config['html']:
    src_path = 'original/' + get_filename_from_url(url, config['base'])
    filename = 'html/' + get_filename_from_url(url, config['base'])
    html_list.append(filename)
    dst = convert(open(src_path).read(), css_list)
    mkdir_if_not_exist(filename)
    file_put_contents(lxml.html.tostring(dst, encoding='utf-8', include_meta_content_type=True), filename)

# TODO このへんまだあやしい
# 目次
if config['index']:
    filename = 'html/' + get_filename_from_url(config['index'], config['base'])
    dst = convert(open(config['index']).read(), css_list)
    config['index'] = filename
    mkdir_if_not_exist(filename)
    file_put_contents(lxml.html.tostring(dst, encoding='utf-8', include_meta_content_type=True), filename)
else:
    dst = lxml.html.fromstring(DEFAULT_PAGE_HTML)
    dst.xpath('//head')[0].append(lxml.html.fromstring(u'<title>目次</title>'))
    for path in html_list:
        html = lxml.html.fromstring(open(path).read())
        title = html.xpath('//title')[0].text_content()
        a = lxml.html.Element('a', {'href':path});
        a.text = title
        dst.xpath('//body')[0].append(a)
        dst.xpath('//body')[0].append(lxml.html.Element('br'))
    file_put_contents(lxml.html.tostring(dst, encoding='utf-8', include_meta_content_type=True, pretty_print=True), 'index.html')
    config['index'] = 'index.html'

# toc.ncx
toc = lxml.etree.fromstring(DEFAULT_TOC_NCX)
ns = {'ncx':'http://www.daisy.org/z3986/2005/ncx/'}
toc.xpath('//ncx:text', namespaces=ns)[0].text = config['title']
navMap = toc.xpath('//ncx:navMap', namespaces=ns)[0]
navMap.append(create_navPoint('index', 0, u'目次', config['index']))
for i, path in enumerate(html_list):
    html = lxml.html.fromstring(open(path).read())
    title = html.xpath('//title')[0].text_content()
    navMap.append(create_navPoint('item'+str(i), i+1, title, path))
file_put_contents(lxml.etree.tostring(toc, encoding='utf-8', xml_declaration=True, pretty_print=True), 'toc.ncx')

# opf
opf = lxml.etree.fromstring(DEFAULT_OPF)
opf.xpath('//dc:Title', namespaces={'dc':'http://purl.org/metadata/dublin_core'})[0].text = config['title']
for navPoint in toc.xpath('//navPoint'):
    item = lxml.etree.Element('item', {
        'id':navPoint.attrib['id'], 
        'href':navPoint.xpath('content')[0].attrib['src'],
        'media-type':'text/x-oeb1-document'})
    opf.xpath('//manifest')[0].append(item)
    if navPoint.attrib['id'].startswith('item'):
        itemref = lxml.etree.Element('itemref', {'idref':navPoint.attrib['id']})
        opf.xpath('//spine')[0].append(itemref)
    if navPoint.attrib['id'] is 'index':
        reference = lxml.etree.Element('reference', {
            'type':'toc',
            'title':'Table of Contents',
            'href':navPoint.xpath('//content')[0].attrib['src']})
        opf.xpath('//guide')[0].append(reference)
    if navPoint.attrib['playOrder'] is '1':
        reference = lxml.etree.Element('reference', {
            'type':'start',
            'title':'Startup Page',
            'href':navPoint.xpath('//content')[0].attrib['src']})
        opf.xpath('//guide')[0].append(reference)
file_put_contents(lxml.etree.tostring(opf, encoding='utf-8', xml_declaration=True, pretty_print=True), config['name']+'.opf')

def create_cover(title):
    canvas = Image.open(os.path.dirname(sys.argv[0]) + '/cover.jpg')
    
    width, height = canvas.size
    max_row_len = 16
    text = textwrap.wrap(title, max_row_len)
    font_size = (width / 10 * 8) / max_row_len
    content_width =  max_row_len * font_size if len(text) > 1 else len(title) * font_size
    left_margin = (width - content_width) / 2
    content_height = len(text) * font_size
    top_margin = (height - content_height) / 2
    
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(config['font'], font_size)
    draw.text((left_margin, top_margin), "\n".join(text), font=font, fill="#000")

    canvas.save('./cover.jpg', 'JPEG', quality=90, optimize=True)


#cover.jpg
create_cover(config['title'])

