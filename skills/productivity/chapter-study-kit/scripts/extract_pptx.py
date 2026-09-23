#!/usr/bin/env python3
"""Extract local PPTX slide text in presentation order; no images or notes."""
import argparse
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def extract(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {rel.attrib['Id']: rel.attrib['Target'] for rel in rels
                   if rel.get('TargetMode') != 'External'}
        slides = presentation.findall('p:sldIdLst/p:sldId', NS)
        if not slides:
            raise ValueError('Presentation contains no slides')
        output = [f'### FILE: {path.name} | slides: {len(slides)}',
                  'TEXT ONLY: inspect images, charts, and speaker notes separately.']
        for number, slide in enumerate(slides, 1):
            target = targets[slide.attrib['{' + NS['r'] + '}id']]
            member = posixpath.normpath('ppt/' + target) if not target.startswith('/') else target.lstrip('/')
            xml = ET.fromstring(archive.read(member))
            paragraphs = [''.join(t.text or '' for t in p.findall('.//a:t', NS))
                          for p in xml.findall('.//a:p', NS)]
            paragraphs = [p for p in paragraphs if p.strip()]
            if not paragraphs:
                raise ValueError(f'Slide {number}: no extractable text; inspect/export locally for OCR')
            output += [f'--- slide {number} ---', *paragraphs]
        return '\n'.join(output) + '\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx', type=Path)
    args = parser.parse_args()
    try:
        result = extract(args.pptx)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        parser.exit(1, f'Extraction failed: {error}\n')
    print(result, end='')


if __name__ == '__main__':
    main()
