# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 20 Apr 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import urllib
import xmltodict as xmld
from stomp.listener import ConnectionListener

from ligmos import utils

from .parser_general import parserFlatPacket, parserSimple


class MesaConsumer(ConnectionListener):
    def __init__(self, dbconn=None):
        """
        This will really be stuffed into a
        utils.amq.amqHelper class, so all the connections stuff is
        really over there in that class.  This is just to route the
        Mesa-specific messages to the right parsers
        """

        # Adding an extra argument to the subclass
        self.dbconn = dbconn

        # Grab all the schemas that are in the ligmos library
        self.schemaDict = utils.amq.schemaDicter()
        print(self.schemaDict)

    def on_message(self, headers, body):
        """
        Basically subclassing stomp.listener.ConnectionListener
        """
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                # Note that I don't care about the actual result, parsing
                #   happens later.  I just want to see if parsing is even
                #   possible at this early stage to help direct the message
                # TECHNICALLY this is a double parse and a hit to CPU usage.
                #   But computers are both fast and cheap so I can be sloppy.
                _ = xmld.parse(body)
                # If we want to have the XML as a string:
                # res = {tname: [headers, dumpPacket(xml)]}
                # If we want to have the XML as an object:
                # res = {tname: [headers, xml]}
                isXML = True
            except xmld.expat.ExpatError:
                # This means that XML wasn't found, so it's just a string
                #   packet with little/no structure. Attach the sub name
                #   as a tag so someone else can deal with the thing
                # res = {tname: [headers, body]}
                isXML = False
            except Exception as err:
                # This means that there was some kind of transport error
                #   or it couldn't figure out the encoding for some reason.
                #   Scream into the log but keep moving
                print("="*42)
                print(headers)
                print(body)
                print(str(err))
                print("="*42)
                badMsg = True
                isXML = False

        # List of topics that we know have schemas and will work.
        #   Still hardcoding things at the moment.
        vFlats = ['lig.mesa.NPOIWeatherStation',
                  'LOUI.nasa42.loisTelemetry']

        # List of topics that we know have a float value and nothing else
        vFloats = []

        # List of topics that are just words/strings
        vStrings = []

        # List of topics that are bools (strings saying true/false)
        vBools = []

        # Now send the packet to the right place for processing.
        #   These need special parsing because they're formatted strings
        if badMsg is False:
            try:
                if tname in vFlats:
                    if isXML is True:
                        # TODO: Wrap this in a proper try...except
                        #   As of right now, it'll be caught in the "WTF!!!"
                        schema = self.schemaDict[tname]
                        print("Schema before call:")
                        print(schema)
                        parserFlatPacket(headers, body,
                                         schema=schema, db=self.dbconn)
                elif tname in vFloats:
                    parserSimple(headers, body, db=self.dbconn,
                                 datatype='float')
                elif tname in vStrings:
                    parserSimple(headers, body, db=self.dbconn,
                                 datatype='string')
                elif tname in vBools:
                    parserSimple(headers, body, db=self.dbconn,
                                 datatype='bool')
                else:
                    # Intended to be the endpoint of the auto-XML publisher
                    #   so I can catch most of them rather than explicitly
                    #   check in the if/elif block above
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
            except urllib.error.URLError as err:
                # This actually implies that the message wasn't a valid XML
                #   message and couldn't actually be validated.  I think it's
                #   really a quirk of the xmlschema library but I'm not sure
                print(err)
            except Exception as err:
                # Mostly this catches instances where the topic name doesn't
                #   have a schema, but it catches all oopsies really
                print("="*11)
                print("WTF!!!")
                print(str(err))
                print(headers)
                print(body)
                print("="*11)
