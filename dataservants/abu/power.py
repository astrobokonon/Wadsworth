# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 1 May 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import xmltodict as xmld

from .helpers import xmlParserCatcher


def parseiSense(msg, rootKey=None):
    """
    Translate the "XML" file that the i-SENSE voltage monitor puts out
    into something that fits easier into the XML schema/parsing way of life.
    """
    pdict = xmlParserCatcher(msg)

    if pdict != {}:
        # There's only ever one root, so just cut to the chase
        pdict = pdict['attributes']

        if rootKey is None:
            rootKey = "isense"

        # Since this is eventually going to become XML, we need to define a
        #   root key for the document; all other tags will live under it
        root = {rootKey: None}

        # Now loop over each individual measurement in the orig. crap packet
        valdict = {}
        for imeas in pdict['attribute']:
            mn = imeas['@id']
            try:
                mv = imeas['#text']
            except KeyError:
                # This means that the attribute had no actual value
                mv = ""

            newEntry = {mn: mv}

            valdict.update(newEntry)

        # Add our values to this station
        root[rootKey] = valdict

        # Now turn it into an XML string so we can pass it along to the broker
        #   using the magic that is xmld's unparse() method
        npacket = xmld.unparse(root, pretty=True)
    else:
        npacket = None

    return npacket
