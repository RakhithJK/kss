# Copyright 2018 David Corbett
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division, unicode_literals

__all__ = ['augment']

import math
import os
import tempfile

import fontforge
import psMat

INTRA_CLUSTER_GAP = 0.04

def cgj(font):
    glyph = font.createChar(0x034F, 'uni034F')
    glyph.glyphclass = b'mark'
    glyph.width = 0

def add_lookups(font):
    font.addLookup("'mkmk'",
        'gpos_mark2mark',
        (),
        ((b'mkmk', ((b'DFLT', ('dflt',)),)),))
    font.addLookupSubtable("'mkmk'", "'mkmk'-1")
    font.addAnchorClass("'mkmk'-1", 'cluster-next')
    font.addLookup("'mark'",
        'gpos_mark2base',
        (),
        ((b'mark', ((b'DFLT', ('dflt',)),)),))
    font.addLookupSubtable("'mark'", "'mark'-1")
    font.addAnchorClass("'mark'-1", 'cluster-init')

def kss1init(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss1init')
    glyph.glyphclass = b'baseglyph'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.scale(1, 0.8))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = nominal_glyph.width
    glyph.addAnchorPoint('cluster-init', 'base', nominal_glyph.width, glyph.boundingBox()[1] - INTRA_CLUSTER_GAP * nominal_glyph.width)

def kss1(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss1')
    glyph.glyphclass = b'mark'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.translate(-nominal_glyph.width, 0))
    glyph.transform(psMat.scale(1, 0.8))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = 0
    glyph.addAnchorPoint('cluster-next', 'basemark', 0, glyph.boundingBox()[1] - INTRA_CLUSTER_GAP * nominal_glyph.width)
    glyph.addAnchorPoint('cluster-next', 'mark', 0, glyph.boundingBox()[3] + INTRA_CLUSTER_GAP * nominal_glyph.width)
    glyph.addAnchorPoint('cluster-init', 'mark', 0, glyph.boundingBox()[3] + INTRA_CLUSTER_GAP * nominal_glyph.width)

def kss2init(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss2init')
    glyph.glyphclass = b'baseglyph'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.scale(0.5, 0.8))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = nominal_glyph.width
    glyph.addAnchorPoint('cluster-init', 'base', nominal_glyph.width, 0)

def kss2(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss2')
    glyph.glyphclass = b'mark'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.translate(-nominal_glyph.width, 0))
    glyph.transform(psMat.scale(0.5, 0.8))
    glyph.transform(psMat.translate(-nominal_glyph.width / 2, 0))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.addAnchorPoint('cluster-next', 'basemark', 0, 0)
    glyph.addAnchorPoint('cluster-next', 'mark', 0, font.ascent)
    glyph.addAnchorPoint('cluster-init', 'mark', 0, font.ascent)
    glyph.width = 0

def kss3(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss3')
    glyph.glyphclass = b'mark'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.translate(-nominal_glyph.width, 0))
    glyph.transform(psMat.scale(0.5, 0.8))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.addAnchorPoint('cluster-next', 'basemark', 0, 0)
    glyph.addAnchorPoint('cluster-next', 'mark', 0, 0)
    glyph.addAnchorPoint('cluster-init', 'mark', 0, 0)
    glyph.width = 0

# The values represent the glyph classes that get contextually
# transformed to the keys. ``None`` represents the nominal glyphs.
TRANSFORMS = {
    kss1init: None,
    kss1: None,
    kss2init: None,
    kss2: kss1,
    kss3: kss1,
}

def augment(font):
    cgj(font)
    add_lookups(font)
    glyph_names = []
    for glyph in font.selection.select((b'ranges', b'unicode'), 0xE000, 0xF8FF).byGlyphs:
        glyph_names.append(glyph.glyphname)
        for transform in TRANSFORMS:
            transform(font, glyph)
    fea_path = tempfile.mkstemp(suffix='.fea')[1]
    try:
        with open(fea_path, 'w') as fea:
            fea.write('languagesystem DFLT dflt;\n\n')
            fea.write('@kss = [{}];\n\n'.format(' '.join(glyph_names)))
            for dst, src in TRANSFORMS.items():
                fea.write('@{cls} = [{}.{cls}];\n\n'.format(
                        '.{} '.format(dst.__name__).join(glyph_names), cls=dst.__name__))
                fea.write('lookup {} {{\n'.format(dst.__name__))
                for glyph_name in glyph_names:
                    fea.write('    substitute {glyph}{src} by {glyph}.{dst};\n'.format(
                            glyph=glyph_name,
                            src='.{}'.format(src.__name__) if src else '',
                            dst=dst.__name__))
                fea.write('}} {};\n\n'.format(dst.__name__))
            fea.write(
                    'feature rclt {\n'
                    "    substitute [@kss1init @kss1 @kss2init] @kss' lookup kss1;\n"
                    "    substitute @kss' lookup kss1init uni034F' @kss;\n"
                    "    substitute @kss' lookup kss2init @kss;\n"
                    '} rclt;\n'
                    '\n'
                    'feature rclt {\n'
                    "    substitute [@kss2init @kss2] @kss1' lookup kss3;\n"
                    "    substitute @kss1' lookup kss2 @kss1;\n"
                    '} rclt;\n')
        font.mergeFeature(fea_path)
    finally:
        os.remove(fea_path)

