#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import ElementMaker
import rauth
import requests
import xmltodict

# "sparse" docs at http://www.doodle.com/xsd1/RESTfulDoodle.pdf
# but hey, i fucking love reading DTDs. http://doodle.com/xsd1/poll.xsd
# this pretty much explains why there hasn't been a single usable library
# for the doodle API in 5 years


class DoodleException(Exception):
    pass


class Doodle(object):
    base_url = 'https://doodle.com/api1'
    doodle_ns = 'http://doodle.com/xsd1'
    public_url = 'https://doodle.com/%s'
    admin_url = 'https://doodle.com/%s%s/admin'

    # obtainable from https://doodle.com/mydoodle/consumer/credentials.html
    def __init__(self, client_key, client_secret):
        self.service = rauth.OAuth1Service(
            name='doodle.com',
            consumer_key=client_key,
            consumer_secret=client_secret,
            request_token_url=self.base_url + '/oauth/requesttoken',
            access_token_url=self.base_url + '/oauth/accesstoken',
        )

    @property
    def session(self):
      if not getattr(self, '_session', None):
        self._new_access_token()
      return self._session

    def _new_access_token(self):
        request = self.service.get_request_token()
        access = self.service.get_access_token(*request)
        self._session = self.service.get_session(access)

    def get_admin_url(self, poll_id, key):
        return self.admin_url % (poll_id, key)

    def get_public_url(self, poll_id):
        return self.public_url % poll_id

    def get_poll(self, poll_id, key=None):
        headers = {}
        if key:
            headers['X-DoodleKey'] = key
        r = self.session.get(self.base_url + '/polls/' + poll_id,
                             headers=headers)
        r.raise_for_status()

        return xmltodict.parse(r.content)['poll']

    def create_poll(self, initiator,
                          title,
                          initiator_email=None,
                          description=None,
                          location=None,
                          type='TEXT',
                          hidden=False,
                          options=[],
                          ):
        """Creates a new poll.

        :param initiator: Name of the initiator.
        :param initiator_email: E-Mail of the initiator. Doodle uses this to
                                attach a poll to an account.
        :param description: The description shown.
        :param location: Optional location. Must be given if description isn't.
        :param type: One of ``'TEXT'`` or ``'DATE'``.
        :param hidden: Hide participant names.
        :param options: An array of strings or ``Option``s. When ``'DATE'`` is
                        chosen for ``type``, must be ``Option`` with date or
                        date_time set.
        """
        assert type in ('TEXT', 'DATE')
        assert location or description
        E = ElementMaker(namespace=self.doodle_ns)
        poll = etree.Element('poll', nsmap={None: self.doodle_ns})
        poll.append(E.type(type))
        poll.append(E.hidden('true' if hidden else 'false'))
        poll.append(E.levels('2'))
        poll.append(E.title(title))

        if description:
            poll.append(E.description(description))
        if location:
            poll.append(E.location(location))

        initiator_elem = E.initiator(E.name(initiator))
        if initiator_email:
            initiator_elem.append(E.eMailAddress(initiator_email))

        poll.append(initiator_elem)

        opts = E.options()
        for opt in options:
            if isinstance(opt, basestring):
                opt = Option(opt)
            opts.append(opt.to_node())

        poll.append(opts)

        r = self.session.post(
            self.base_url + '/polls',
            data=etree.tostring(poll),
            headers={'Content-type': 'application/xml'},
        )

        r.raise_for_status()

        return r.headers['Content-Location'], r.headers['X-DoodleKey']


class Option(object):
    def __init__(self, value=None, date=None, date_time=None, start=None,
                   end=None):
        """Options for a poll

        All options should be passed as naive datetimes because strange
        things happen if actual timezones are passed. Just don't.

        :param value: The text to show.
        :param date: A date object, the time in question.
        :param date_time: A datetime object, instead of ``date``.
        :param start: Start time, should also pass ``end`` and none of
                      ``date`` or ``date_time``.
        :param end: End time, like ``start`` should be a datetime object.
        """
        self.value = value
        self.date = date
        self.date_time = date_time
        self.start = start
        self.end = end

    def to_node(self):
        option = etree.Element('option', nsmap={None: Doodle.doodle_ns})

        if self.date:
            option.set('date', self.date.isoformat())

        if self.date_time:
            option.set('dateTime', self.date_time.isoformat())

        if self.start:
            option.set('startDateTime', self.start.isoformat())

        if self.end:
            option.set('end', self.end)

        if self.value:
            option.text = self.value

        return option
