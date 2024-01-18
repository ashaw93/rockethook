"""Simple library for posting to Rocket.Chat via webhooks a.k.a. integrations.

The idea behind this library is to create Webhook object and then
post Messages with it. You can create Message object and fulfill it
with content (text and/or attachments) later.

Or you can just Webhook.quick_post('Your message') without bothering with Message objects.
"""

import json
import requests
import urllib
import traceback
from urllib.parse import urlparse


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
    >>> msg.add_attachment(
    ...     title='Attach',
    ...     title_link='http://example.com',
    ...     image_url='http://example.com/img.png'
    ... )
    >>> my_hook.post(msg)
    >>>
    >>> my_hook.quick_post('Hi!')
    >>> my_hook.quick_post('What\'s up?')
    """
    def __init__(self, server_url, token, send_msg_timeout_secs: int = 30):
        """ Creates Webhook suitable for posting multiple messages.

        server_url should be a valid URL starting with scheme.
        token is a token given by a Rocket.Chat server.
        """
        parsed = urlparse(server_url)
        self.scheme = parsed.scheme
        if parsed.netloc:
            self.server_fqdn = parsed.netloc
        else:
            self.server_fqdn = parsed.path.split('/')[0]
        self.token = token
        self.send_msg_timeout_secs = send_msg_timeout_secs

    def quick_post(self, text):
        """Method for posting simple text messages."""
        self.post(Message(text=text))

    def post(self, message):
        """Send your message to Rocket.Chat.

        message argument is expected to be a rockethook.Message object.
        If you want to just post simple text message, please use quick_post() method.
        """

        assert type(message) is Message, 'Error: message is not a rockethook.Message'

        payload_dict = {}
        if message.text:
            payload_dict['text'] = message.text
        if message.channel:
            payload_dict['channel'] = message.channel
        if message.icon_url:
            payload_dict['icon_url'] = message.icon_url
        if message.attachments:
            payload_dict['attachments'] = message.attachments
        payload = 'payload=' + urllib.parse.quote_plus(json.dumps(payload_dict))
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}


        try:
            response = requests.post(f"{self.scheme}://{self.server_fqdn}/hooks/{self.token}", data=payload, headers=headers, timeout=self.send_msg_timeout_sec)
            status_code = response.status_code
            data = response.json()
            if status_code != 200:
                if "error" in data:
                    err_msg = data["error"]
                elif "message" in data:
                    err_msg = data["message"]
                else:
                    err_msg = data
                raise WebhookError(response.status_code, err_msg)
        except requests.Timeout:
            raise WebhookError(-1, 'Timeout while sending Rocket message')
        except requests.ConnectionError:
            raise WebhookError(-1, 'Unable to connect to Rocket API')
        except:
            raise WebhookError(-1, f"Unknown exception while sending Rocket message: {traceback.format_exc()}")

class Message(object):
    """Usage example:

    >>> import rockethook
    >>> my_hook = rockethook.Webhook('https://rocketchat.example.com', token)
    >>> msg = rockethook.Message(icon_url='http://example.com/icon.png')
    >>> msg.append_text('First line.')
    >>> msg.append_text('Second line.')
    >>> msg.add_attachment(
    ...     title='Attach',
    ...     title_link='http://example.com',
    ...     image_url='http://example.com/img.png'
    ... )
    >>> my_hook.post(msg)
    """
    def __init__(self, text='', channel=None, icon_url=None):
        """ Creates Message.

        You can create a Message and fulfill it with content at the same time like this:
        >>> msg = rockethook.Message(text='Hi there')

        Or you can create a Message and then add text and attachments to it later.
        """
        self.text = text
        self.channel = channel
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

        As of Rocket.Chat version 0.20, valid attachment arguments are the following:
            * title
            * title_link
            * text
            * image_url
            * color
        You can have multiple attachments in a single message.
        """
        self.attachments.append(kwargs)
