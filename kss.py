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
import re
import tempfile

import fontforge
import psMat

CLUSTER_Y_SCALE = 0.8
MAX_EXTRA_ROWS = 3
INTRA_CLUSTER_GAP = 0.04
VERSION = '1.000'
FONT_NAME = 'Khitan Small Stacked'
COPYRIGHT = '''Copyright (c) 2018, David Corbett (corbett.dav@husky.neu.edu).
Copyright (c) 2013, Andrew West (www.babelstone.co.uk).'''
LICENSE = '''Copyright (c) 2018, David Corbett (corbett.dav@husky.neu.edu).
Copyright (c) 2013, Andrew West (www.babelstone.co.uk),
with Reserved Font Name BabelStone.

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at:
http://scripts.sil.org/OFL


-----------------------------------------------------------
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
-----------------------------------------------------------

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership
with others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The
fonts, including any derivative works, can be bundled, embedded,
redistributed and/or sold with any software provided that any reserved
names are not used by derivative works. The fonts and derivatives,
however, cannot be released under any other type of license. The
requirement for fonts to remain under this license does not apply
to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright
Holder(s) under this license and clearly marked as such. This may
include source files, build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the
copyright statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting,
or substituting -- in part or in whole -- any of the components of the
Original Version, by changing formats or by porting the Font Software to a
new environment.

"Author" refers to any designer, engineer, programmer, technical
writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining
a copy of the Font Software, to use, study, copy, merge, embed, modify,
redistribute, and sell modified and unmodified copies of the Font
Software, subject to the following conditions:

1) Neither the Font Software nor any of its individual components,
in Original or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy
contains the above copyright notice and this license. These can be
included either as stand-alone text files, human-readable headers or
in the appropriate machine-readable metadata fields within text or
binary files as long as those fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font
Name(s) unless explicit written permission is granted by the corresponding
Copyright Holder. This restriction only applies to the primary font name as
presented to the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
Software shall not be used to promote, endorse or advertise any
Modified Version, except to acknowledge the contribution(s) of the
Copyright Holder(s) and the Author(s) or with their explicit written
permission.

5) The Font Software, modified or unmodified, in part or in whole,
must be distributed entirely under this license, and must not be
distributed under any other license. The requirement for fonts to
remain under this license does not apply to any document created
using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are
not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.'''

def cgj(font):
    glyph = font.createChar(0x034F, 'uni034F')
    glyph.glyphclass = b'mark'
    glyph.width = 0

def zwsp(font):
    glyph = font.createChar(0x200B, 'uni200B')
    glyph.glyphclass = b'baseglyph'
    glyph.width = 0
    glyph = font.createChar(-1, 'uni200B.1')
    glyph.glyphclass = b'baseglyph'
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

def recreate_names(font):
    font.copyright = COPYRIGHT
    font.familyname = FONT_NAME
    font.fontname = re.sub(r"[^!-$&'*-.0-;=?-Z\\^-z|~]+", '', FONT_NAME)
    font.fullname = FONT_NAME
    font.sfntRevision = None
    font.version = VERSION
    font.sfnt_names = (
            (b'English (US)', b'SubFamily', 'Regular'),
            (b'English (US)', b'UniqueID', '{}:{}'.format(font.fullname, font.version)),
            (b'English (US)', b'License', LICENSE),
            (b'English (US)', b'License URL', 'http://scripts.sil.org/OFL'),
        )

def kss1init(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss1init')
    glyph.glyphclass = b'baseglyph'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.scale(1, CLUSTER_Y_SCALE))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = nominal_glyph.width
    glyph.addAnchorPoint('cluster-init', 'base', nominal_glyph.width, glyph.boundingBox()[1] - INTRA_CLUSTER_GAP * nominal_glyph.width)

def kss1(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss1')
    glyph.glyphclass = b'mark'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.translate(-nominal_glyph.width, 0))
    glyph.transform(psMat.scale(1, CLUSTER_Y_SCALE))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = 0
    glyph.addAnchorPoint('cluster-next', 'basemark', 0, glyph.boundingBox()[1] - INTRA_CLUSTER_GAP * nominal_glyph.width)
    glyph.addAnchorPoint('cluster-next', 'mark', 0, glyph.boundingBox()[3] + INTRA_CLUSTER_GAP * nominal_glyph.width)
    glyph.addAnchorPoint('cluster-init', 'mark', 0, glyph.boundingBox()[3] + INTRA_CLUSTER_GAP * nominal_glyph.width)

def kss2init(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss2init')
    glyph.glyphclass = b'baseglyph'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.scale(0.5, CLUSTER_Y_SCALE))
    glyph.transform(psMat.translate(0, nominal_glyph.boundingBox()[3] - glyph.boundingBox()[3]))
    glyph.width = nominal_glyph.width
    glyph.addAnchorPoint('cluster-init', 'base', nominal_glyph.width, 0)

def kss2(font, nominal_glyph):
    glyph = font.createChar(-1, nominal_glyph.glyphname + '.kss2')
    glyph.glyphclass = b'mark'
    nominal_glyph.draw(glyph.glyphPen())
    glyph.transform(psMat.translate(-nominal_glyph.width, 0))
    glyph.transform(psMat.scale(0.5, CLUSTER_Y_SCALE))
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
    glyph.transform(psMat.scale(0.5, CLUSTER_Y_SCALE))
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
    zwsp(font)
    add_lookups(font)
    recreate_names(font)
    font.hhea_linegap = int((MAX_EXTRA_ROWS - (1 - CLUSTER_Y_SCALE)) * font.ascent)
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
                    'feature ccmp {\n'
                    '    substitute uni200B by uni200B.1 uni200B.1;\n'
                    '} ccmp;\n'
                    '\n'
                    'feature ccmp {\n'
                    '    substitute uni200B.1 uni200B.1 by uni200B;\n'
                    '} ccmp;\n'
                    '\n'
                    'feature ccmp {\n'
                    "    substitute [@kss1init @kss1 @kss2init] @kss' lookup kss1;\n"
                    "    substitute @kss' lookup kss1init uni034F' @kss;\n"
                    "    substitute @kss' lookup kss2init @kss;\n"
                    '} ccmp;\n'
                    '\n'
                    'feature ccmp {\n'
                    "    substitute [@kss2init @kss2] @kss1' lookup kss3;\n"
                    "    substitute @kss1' lookup kss2 @kss1;\n"
                    '} ccmp;\n'
                    '\n'
                    'feature mark {\n')
            for is_kss1init in [True, False]:
                for rows in range(MAX_EXTRA_ROWS, 0, -1):
                    y = int((rows - (1 - CLUSTER_Y_SCALE)) * font.ascent)
                    if is_kss1init:
                        fea.write("    position @kss1init' <0 {} 0 0>".format(y))
                    else:
                        fea.write("    position @kss2init' <0 {} 0 0> @kss3".format(y))
                    fea.write(' @kss2 @kss3' * (rows - 1))
                    fea.write(' [@kss1 @kss2];\n')
            fea.write('} mark;\n')
        font.mergeFeature(fea_path)
    finally:
        os.remove(fea_path)

