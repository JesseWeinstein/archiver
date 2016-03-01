#!/usr/bin/env python3


import json
import os
import re
import sys


import markdown


class Article:
    ''''''
    title = None
    authors = []
    short_reference = None
    volume = None
    number = None
    toc = None
    chapter = None
    excerpt = None
    contents = []
    supernotes = []

    def __init__(self, file, volume, number):
        self.contents = []
        self.title = file.content['metadata']['title']
        if 'author' in file.content['metadata']:
            self.authors = file.content['metadata']['author']
        else:
            self.authors = []
        self.short_reference = file.content['metadata']['short-reference']
        self.toc = file.content['metadata']['position']
        if 'chapter' in file.content['metadata']:
            self.chapter = file.content['metadata']['chapter']
        if 'summary' in file.content['metadata']:
            self.excerpt = file.content['metadata']['summary']
        self.volume = volume
        self.number = number

        map_counter = 0
        for element in file.content['content']:
            if element['type'] in \
                ['paragraph', 'editorial-intro-paragraph',
                    'alt-voice-paragraph', 'blockquote',
                    'stage-direction-paragraph']:
                self.contents.append(Paragraph(element, self))
            elif element['type'] == 'image':
                self.contents.append(Image(element, self))
            elif element['type'] in ['major-divider', 'minor-divider']:
                self.contents.append(Divider(element, self))
            elif element['type'] in ['major-header', 'minor-header']:
                self.contents.append(Header(element, self))
            elif element['type'] == 'anvil-gallery':
                self.contents.append(ImageGallery(element, self))
            elif element['type'] == 'audio':
                self.contents.append(Audio(element, self))
            elif element['type'] == 'video':
                self.contents.append(Video(element, self))
            elif element['type'] == 'table':
                self.contents.append(Table(element, self))
            elif element['type'] == 'map':
                self.contents.append(Map(element, map_counter, self))
                map_counter += 1

    def output(self):
        issue_directory = "issue-{}-{}".format(self.volume, self.number)
        try:
            os.mkdir(issue_directory)
        except Exception:
            pass
        os.chdir(issue_directory)

        try:
            os.mkdir(self.short_reference)
        except Exception:
            pass
        os.chdir(self.short_reference)

        f = open('web_content.html', 'w')
        for element in self.contents:
            f.write(element.output())
            f.write('\n\n')
        f.close()

        f = open('metadata.yml', 'w')
        f.write('---\n')
        f.write('layout: article\n')
        f.write('title: {}\n'.format(self.title))
        f.write('authors:\n')
        f.write('excerpt: >\n')
        f.write('\t{}\n'.format(self.excerpt))
        f.write('permalink: \n')
        f.write('toc: {}\n'.format(self.toc))
        if self.chapter:
            f.write('chapter: {}\n'.format(self.chapter))
        f.write('volume: {}\n'.format(self.volume))
        f.write('number: {}\n'.format(self.number))
        f.write('---\n')
        f.close()


class Paragraph:
    article = None
    content = None
    number = None
    style = None
    internal_links = None

    def __init__(self, data, article):
        self.content = markdown.markdown(data['content'])[3:-4]
        self.number = int(data['number'])
        self.article = article
        self.style = data['type']
        if 'internal-links' in data:
            self.internal_links = data['internal-links']

    def output(self):
        result = '<!-- {} -->\n'.format(self.number)
        if self.style == 'editorial-intro-paragraph':
            wrapper = '<p id="paragraph-{}" class="editorial-intro">\n{}\n</p>'
        elif self.style == 'blockquote':
            wrapper = '<blockquote id="paragraph-{}">\n<p>\n{}\n</p>\n' \
                '</blockquote>'
        elif self.style == 'alt-voice-paragraph':
            wrapper = '<p id="paragraph-{}" class="alternate-voice">\n{}\n</p>'
        elif self.style == 'stage-direction-paragraph':
            wrapper = '<p id="paragraph-{}" class="stage-direction">\n{}\n</p>'
        else:
            wrapper = '<p id="paragraph-{}">\n{}\n</p>'

        result += wrapper.format(self.number, self.content)

        if self.internal_links:
            for internal_link in self.internal_links:
                result = result.replace(
                    internal_link['token'],
                    internal_link['web'])

        return result


class Audio:
    article = None

    def __init__(self, data, article):
        self.article = article
        self.url = data['url'][45:]
        self.label = markdown.markdown(data['label'])[3:-4]

    def output(self):
        result = '<div class="inline-audio">'
        result += '<a href="/audio{}" class="sm2_button">{}</a>' \
            .format(self.url, self.label)
        result += '<p class="label">{}</p>'.format(self.label)
        result += '</div>'

        return result


class Video:
    article = None

    def __init__(self, data, article):
        self.article = article
        self.video_id = data['id']
        self.width = data['width']
        self.height = data['height']
        if 'caption' in data:
            self.caption = markdown.markdown(data['caption'])[3:-4]
        else:
            self.caption = None

    def output(self):
        result = '<div class="inline-video">\n'
        result += '<iframe width="{}" height="{}" ' \
            .format(self.width, self.height)
        result += 'src="https://www.youtube.com/embed/{}'.format(self.video_id)
        result += '?rel=0&amp;showinfo=0" frameborder="0" '
        result += 'allowfullscreen></iframe>\n'
        if self.caption and len(self.caption) > 0:
            result += '<p class="caption">{}</p>\n'.format(self.caption)
        result += '</div>\n'

        return result


class Map:
    article = None
    id = None
    tileset = None
    center = None
    zoom = None
    minZoom = None
    maxZoom = None
    markers = None

    def __init__(self, data, id, article):
        self.article = article
        self.id = id
        self.tileset = data['tileset']
        self.center = (data['center'][0], data['center'][1])
        self.zoom = data['zoom']
        self.minZoom = data['minZoom']
        self.maxZoom = data['maxZoom']
        self.markers = data['markers']

    def map_initialization(self):
        result = 'var leaflet_map_id_{} = "map-container-{}";\n' \
            .format(self.id, self.id)
        result += 'var leaflet_layer_{} = new L.StamenTileLayer("{}");\n' \
            .format(self.id, self.tileset)
        result += 'var leaflet_map_{} = L.map(leaflet_map_id_{}, {{\n' \
            .format(self.id, self.id)
        result += 'center: new L.LatLng({}, {}), ' \
            .format(self.center[0], self.center[1])
        result += 'zoom: {}, '.format(self.zoom)
        result += 'minZoom: {}, '.format(self.minZoom)
        result += 'maxZoom: {}'.format(self.maxZoom)
        result += '});\n'

        result += "leaflet_map_{}.attributionControl.addAttribution(" \
            "'Map tiles by <a href=\"http://stamen.com\">Stamen Design</a>, " \
            "under <a href=\"http://creativecommons.org/licenses/by/3.0\">" \
            "CC BY 3.0</a>. Data by <a href=\"http://openstreetmap.org\">" \
            "OpenStreetMap</a>, under <a href=\"http://creativecommons.org/" \
            "licenses/by-sa/3.0\">CC BY SA</a>.');\n".format(self.id)

        result += 'leaflet_map_{}.addLayer(leaflet_layer_{});\n' \
            .format(self.id, self.id)

        return result

    def output(self):
        result = '<div id="map-container-{}" class="inline-leaflet-map" \
                    ></div>\n'.format(self.id)
        result += '<script type=\"text/javascript\">\n'
        result += "$(document).on('ready', function() {\n"
        result += self.map_initialization()
        for mm in self.markers:
            result += 'L.marker([{},{}]).addTo(leaflet_map_{})' \
                      '.bindPopup("{}");\n' \
                      .format(mm['position']['latitude'],
                              mm['position']['longitude'],
                              self.id,
                              mm['message'])
        result += '});\n'
        result += '</script>\n\n'

        return result


class Table:
    article = None

    def __init__(self, data, article):
        self.article = article
        self.title = data['title']
        self.contents = data['contents']

    def output(self):
        result = '<table>\n'
        result += '<caption>{}</caption>\n'.format(self.title)
        result += '<tbody>\n'
        first_row = True
        for row in self.contents:
            result += '<tr>\n'

            if first_row:
                cell_label = 'th'
                first_row = False
            else:
                cell_label = 'td'

            first_cell = True
            for cell in row:
                if first_cell:
                    cell_class = ' class="special"'
                else:
                    cell_class = ''

                result += '<{}{}>{}</{}>\n'.format(
                    cell_label,
                    cell_class,
                    cell,
                    cell_label)
                first_cell = False

            result += '</tr>\n'

        result += '</tbody>\n'
        result += '</table>\n'

        return result


class ImageGallery:
    article = None
    group_id = None
    images = []

    def __init__(self, data, article):
        self.article = article
        self.images = []
        self.group = data['group']
        for image in data['images']:
            self.images.append(Image(image, self.article))

    def output(self):
        result = '<ul class="image-gallery"><!--'
        for image in self.images:
            result += '--><li data-caption="{}" data-credit="{}">'.format(
                image.caption, image.credit)
            result += '<a class="fancybox" rel="{}" '.format(self.group) + \
                'title="{}<span class=\'credit\'>{}</span>" '.format(image.caption, image.credit) + \
                'href="/images/issues/{}/{}/large-{}">'.format(
                    self.article.volume, self.article.number,
                    image.url_template)
            result += '<img src="/images/issues/{}/{}/thumb-{}" ' \
                .format(self.article.volume, self.article.number, image.url_template) + \
                'width="100" alt="{}" />'.format(image.alt)
            result += '</a></li><!--'

        result += '--></ul>'

        return result


class Image:
    article = None
    url_template = None
    alt = None
    caption = None
    credit = None
    float_left = None
    alt_voice = None

    def __init__(self, data, article):
        if 'alt' in data:
            self.alt = data['alt']
        if 'caption' in data:
            self.caption = markdown.markdown(data['caption'])[3:-4]
        if 'credit' in data:
            self.credit = markdown.markdown(data['credit'])[3:-4]
        if 'float' in data:
            self.float_left = True
        if 'alt-voice' in data:
            self.alt_voice = True

        self.url_template = re.split('/', data['url-format'])[-1]

        self.article = article

    def output(self):
        if self.float_left:
            result = '<div class="float-image left">'
        elif self.alt_voice:
            result = '<div class="alternate-voice inline-image">'
        else:
            result = '<div class="inline-image">\n'

        result += \
            '<a class="fancybox" href="/images/issues/{}/{}/large-{}">\n' \
            .format(self.article.volume, self.article.number,
                    self.url_template)
        result += \
            '<img src="/images/issues/{}/{}/medium-{}" ' \
            'alt="{}" />\n' \
            .format(self.article.volume, self.article.number,
                    self.url_template, self.alt)
        result += '</a>\n'

        caption_condition = self.caption and len(self.caption) > 0
        credit_condition = self.credit and len(self.credit) > 0

        if caption_condition or credit_condition:
            result += '<p class="caption">\n'
            if caption_condition:
                result += self.caption + '\n'
            if credit_condition:
                result += \
                    '<span class="credit">{}</span>\n'.format(self.credit)
            result += '</p>\n'
        result += '</div>'

        return result


class Divider:
    article = None
    style = None

    def __init__(self, data, article):
        self.style = data['type']
        self.article = article

    def output(self):
        if self.style == 'major-divider':
            result = '<hr class="special" />'
        elif self.style == 'minor-divider':
            result = '<hr />'
        else:
            result = ''

        return result


class Header:
    article = None
    style = None
    content = None

    def __init__(self, data, article):
        self.article = article
        if data['type'] == 'major-header':
            self.style = 'major'
        elif data['type'] == 'minor-header':
            self.style = 'minor'
        self.content = markdown.markdown(data['content'])[3:-4]

    def output(self):
        if self.style == 'major':
            result = '<h3>{}</h3>'.format(self.content)
        elif self.style == 'minor':
            result = '<h5>{}</h5>'.format(self.content)

        return result


class ContentFile:
    '''Representation of production content file in Appendix JSON format.'''
    stream = None
    content = None

    def __init__(self, stream):
        self.stream = stream
        self.content = json.loads(self.stream.read())


if __name__ == '__main__':
    content_files = []
    skipped_names = [
        'contributors', 'cover.jpg', 'bundle.json',
        'cover-chapter-1.jpg', 'cover-chapter-2.jpg',
        'cover-chapter-3.jpg']
    issue = None
    number = None

    for idx, arg in enumerate(sys.argv):
        # Expects 3+ command line arguments:
        # volume number
        # issue number
        # path(s) to JSON files for article content
        if idx == 0:
            pass
        elif idx == 1:
            issue = arg
        elif idx == 2:
            number = arg
        else:
            name = arg.split('/')[-1]
            if name not in skipped_names:
                content_files.append(ContentFile(open(arg)))

    current_directory = os.getcwd()
    for file in content_files:
        os.chdir(current_directory)
        article = Article(file, issue, number)
        article.output()
