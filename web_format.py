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

    def __init__(self, data, article):
        self.content = markdown.markdown(data['content'])[3:-4]
        self.number = int(data['number'])
        self.article = article
        self.style = data['type']

    def output(self):
        result = '<!-- {} -->\n'.format(self.number)
        if self.style == 'editorial-intro-paragraph':
            wrapper = '<p class="editorial-intro">\n{}\n</p>'
        elif self.style == 'blockquote':
            wrapper = '<blockquote>\n<p>\n{}\n</p>\n</blockquote>'
        elif self.style == 'alt-voice-paragraph':
            wrapper = '<p class="alternate-voice">\n{}\n</p>'
        elif self.style == 'stage-direction-paragraph':
            wrapper = '<p class="stage-direction">\n{}\n</p>'
        else:
            wrapper = '<p>\n{}\n</p>'

        result += wrapper.format(self.content)

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
