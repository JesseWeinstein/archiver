#!/usr/bin/env python3


import json
import os
import re
import sys


class SupernotesCollection:
    """Collects all of the supernotes associated with an article."""

    short_reference = None
    volume = None
    number = None
    paragraphs = []

    def __init__(self, file, volume, number):
        """
        Construct SupernotesCollection.

        Use file containing supernotes JSON data and volume and number
        for issue.
        """
        self.short_reference = file.content['metadata']['short-reference']
        self.volume = volume
        self.number = number
        self.paragraphs = []

        paragraph_keys = list(file.content['supernotes'].keys())
        # Want the numerical sort order, not string order
        paragraph_keys = [int(x) for x in paragraph_keys]
        paragraph_keys.sort()

        for element in paragraph_keys:
            paragraph_collection = file.content['supernotes'][str(element)]

            self.paragraphs.append(
                Paragraph(paragraph_collection, element, self))

    def generate_supernotes(self):
        result = ''
        result += '[\n'
        for p in self.paragraphs:
            result += p.output()
        result = result[:-2] + '\n'
        result += ']'

        return result

    def output(self):
        """Cycle through paragraphs and output them."""
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

        f = open('supernotes.json', 'w')
        f.write(self.generate_supernotes())
        f.close()


class Paragraph:
    """Collects all supernotes on a paragraph identified by number."""

    collection = None
    content = None
    number = None
    notes = []

    def __init__(self, data, number, collection):
        """
        Construct Paragraph.

        Take data and append appropriate set of supernotes to notes list.
        """
        self.number = number
        self.collection = collection
        self.notes = []

        ordered_keys = [['commentary', CommentarySet],
                        ['citation', CitationSet],
                        ['image', ImageSet],
                        ['map', MapSet],
                        ['link', LinkSet],
                        ['video', VideoSet]]

        for key in ordered_keys:
            if key[0] in data:
                self.notes.append(
                    key[1](data[key[0]], collection))

    def output(self):
        result = ''
        result += '{\n'
        result += '"paragraph": {},\n'.format(self.number)
        result += '"notes": [\n'
        for note in self.notes:
            result += note.output()
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class CommentarySet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []

        for comment in data:
            self.content.append(comment)

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "commentary",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += '"{}",\n'.format(element)
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class CitationSet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []

        for citation in data:
            self.content.append(citation)

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "citation",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += '"{}",\n'.format(element)
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class ImageSet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []
        for image in data:
            self.content.append(
                Image(image, collection))

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "image",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += element.output()
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class Image:
    collection = None
    url = None
    alt = None
    credit = None
    caption = None

    def __init__(self, data, collection):
        for field in ['url-format', 'alt', 'credit', 'caption']:
            if field in data:
                if field == 'url-format':
                    self.url = re.split('/', data[field])[-1]
                else:
                    setattr(self, field, data[field])

    def output(self):
        result = ''
        result += '{\n'
        result += '"url": "{}",\n'.format(self.url)
        result += '"alt": "{}",\n'.format(self.alt)
        result += '"caption": "{}",\n'.format(self.caption)
        result += '"credit": "{}"\n'.format(self.credit)
        result += '},\n'

        return result


class MapSet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []
        for map in data:
            self.content.append(
                Map(map, collection))

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "map",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += element.output()
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class Map:
    collection = None
    tileset = None
    center = {}
    zoom = None
    minZoom = None
    maxZoom = None
    markers = []

    def __init__(self, data, collection):
        for field in ['tileset', 'center', 'zoom',
                      'minZoom', 'maxZoom', 'markers']:
            setattr(self, field, data[field])

    def output(self):
        result = ''
        result += '{\n'
        result += '"tileset": "{}",\n'.format(self.tileset)
        result += '"center": {\n'
        result += '"longitude": "{}",\n'.format(self.center['longitude'])
        result += '"latitude": "{}",\n'.format(self.center['latitude'])
        result += '},\n'
        result += '"zoom": "{}",\n'.format(self.zoom)
        result += '"minZoom": "{}",\n'.format(self.minZoom)
        result += '"maxZoom": "{}",\n'.format(self.maxZoom)
        result += '"markers": [\n'
        for marker in self.markers:
            result += '{\n'
            result += '"position": {\n'
            result += '"longitude": "{}",\n'.format(
                marker['position']['longitude'])
            result += '"latitude": "{}"\n'.format(
                marker['position']['latitude'])
            result += '},\n'
            result += '"message": "{}"\n'.format(marker['message'])
            result += '},\n'
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class LinkSet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []
        for link in data:
            self.content.append(
                Link(link, collection))

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "link",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += element.output()
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class Link:
    collection = None
    label = None
    url = None

    def __init__(self, data, collection):
        self.collection = collection
        self.label = data['label']
        self.url = data['url']

    def output(self):
        result = ''
        result += '{\n'
        result += '"label": "{}",\n'.format(self.label)
        result += '"url": "{}"\n'.format(self.url)
        result += '},\n'

        return result


class VideoSet:
    collection = None
    content = []

    def __init__(self, data, collection):
        self.collection = collection
        self.content = []
        for video in data:
            self.content.append(
                Video(video, collection))

    def output(self):
        result = ''
        result += '{\n'
        result += '"type": "video",\n'
        result += '"notes": [\n'
        for element in self.content:
            result += element.output()
        result = result[:-2] + '\n'
        result += ']\n'
        result += '},\n'

        return result


class Video:
    collection = None
    service = None
    id = None
    width = None
    height = None
    caption = None

    def __init__(self, data, collection):
        self.collection = collection
        for field in ['service', 'id', 'width', 'height', 'caption']:
            setattr(self, field, data[field])

    def output(self):
        result = ''
        result += '{\n'
        result += '"service": "{}",\n'.format(self.service)
        result += '"id": "{}",\n'.format(self.id)
        result += '"width": "{}",\n'.format(self.width)
        result += '"height": "{}",\n'.format(self.height)
        result += '"caption": "{}"\n'.format(self.caption)
        result += '},\n'

        return result


class ContentFile:
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
    volume = None
    number = None

    for idx, arg in enumerate(sys.argv):
        if idx == 0:
            pass
        elif idx == 1:
            volume = arg
        elif idx == 2:
            number = arg
        else:
            name = arg.split('/')[-1]
            if name not in skipped_names:
                content_files.append(ContentFile(open(arg)))

    current_directory = os.getcwd()
    for file in content_files:
        os.chdir(current_directory)
        if 'supernotes' in file.content:
            collection = SupernotesCollection(file, volume, number)
            collection.output()
