"""Simple library for posting to Rocket.Chat via webhooks a.k.a. integrations."""

import json
import httplib
import urllib


class WebhookError(Exception):
    """Raised when Rocket.Chat server responses with non-JSON or with an explicit error."""
    def __init__(self, status, message):
        self.status = status
        self.message = 'Rocket.Chat server error, code {0}: {1}'.format(status, message)
        super(WebhookError, self).__init__(self.message)


class Webhook(object):
    """Usage example:

    >>> import rockethook
    >>> my_hook = rockethook.Webhook('https://rocketchat.example.com', token)
    >>> msg = rockethook.Message(icon_url='http://example.com/icon.png')
    >>> msg.append_text('First line.')
    >>> msg.append_text('Second line.')
    >>> msg.add_attachment(title='Attach', title_link='http://example.com', image_url='http://example.com/img.png')
    >>> my_hook.post(msg)
    >>>
    >>> my_hook.quick_post('Hi!')
    >>> my_hook.quick_post('What\'s up?')
    """
    def __init__(self, server_url, token):
        if server_url.split('://')[0] == 'https':
            self.https = True
        else:
            self.https = False
        self.server_fqdn = server_url.split('://')[-1].replace('/', '')
        self.token = token

    def quick_post(self, text):
        """Method for posting simple text messages."""
        self.post(Message(text))

    def post(self, message):
        """Send your message to Rocket.Chat.

        message argument is expected to be a rockethook.Message object.
        If you want to just post simple text message, please use quick_post() method.
        """

        assert type(message) is Message, 'Error: message is not a rockethook.Message'

        payload_dict = {}
        if message.text:
            payload_dict['text'] = message.text
        if message.icon_url:
            payload_dict['icon_url'] = message.icon_url
        if message.attachments:
            payload_dict['attachments'] = message.attachments
        payload = 'payload=' + urllib.quote_plus(json.dumps(payload_dict))
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        if self.https:
            conn = httplib.HTTPSConnection(self.server_fqdn)
        else:
            conn = httplib.HTTPConnection(self.server_fqdn)
        conn.request('POST', '/hooks/' + self.token, payload, headers)
        response = conn.getresponse()
        status = response.status
        response_data = response.read()
        conn.close()
        try:
            data = json.loads(response_data)
        except:
            raise WebhookError(response.status, 'Not an API response, check your token.')
        if status != 200:
            raise WebhookError(response.status, data['message'])


class Message(object):
    """Usage example:

    >>> import rockethook
    >>> my_hook = rockethook.Webhook('https://rocketchat.example.com', token)
    >>> msg = rockethook.Message(icon_url='http://example.com/icon.png')
    >>> msg.append_text('First line.')
    >>> msg.append_text('Second line.')
    >>> msg.add_attachment(title='Attach', title_link='http://example.com', image_url='http://example.com/img.png')
    >>> my_hook.post(msg)
    """
    def __init__(self, text='', icon_url=None):
        self.text = text
        self.icon_url = icon_url
        self.attachments = []

    def append_text(self, text_to_append, delimiter='\n'):
        """Add new text to the message."""
        if self.text:
            self.text = self.text + delimiter + text_to_append
        else:
            self.text = text_to_append

    def add_attachment(self, **kwargs):
        """Add an attachment to the message.

        As of Rocket.Chat version 0.17, valid attachment arguments are the following:
            * title
            * title_link
            * text
            * image_url
            * color
        You can have multiple attachments in a single message.
        """
        self.attachments.append(kwargs)