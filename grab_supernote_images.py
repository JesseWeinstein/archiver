#!/usr/bin/env python3


import json
import os
import sys


class ContentFile:
    stream = None
    content = None

    def __init__(self, stream):
        self.stream = stream
        self.content = json.loads(self.stream.read())


def generate_img_names(file):
    result = ''

    wrapper = 'http://s3.amazonaws.com/appendixjournal-images' + \
        '/images/attachments{}\n'

    for key in file.content['supernotes'].keys():
        paragraph = file.content['supernotes'][key]

        if 'image' in paragraph:
            thumbnail_flag = len(paragraph['image']) > 1
            for image in paragraph['image']:
                result += wrapper.format(
                    image['url-format'].replace('***', 'medium'))
                result += wrapper.format(
                    image['url-format'].replace('***', 'large'))
                if thumbnail_flag:
                    result += wrapper.format(
                        image['url-format'].replace('***', 'thumbnail'))

    return result


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
    result = ''
    for file in content_files:
        os.chdir(current_directory)
        if 'supernotes' in file.content:
            result += generate_img_names(file)

    print(result)
