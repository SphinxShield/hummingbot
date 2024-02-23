from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class Slacker():
    def __init__(self, logger, slack_token, channel='hb-monitor'):
        try:
            self.initialised = False
            self.logger = logger
            self.channel = channel
            self.client = WebClient(token=slack_token)
            self.initialised = True
        except Exception as e:
            self.logger.error("Failed to initialise Slacker")
            self.logger.error(e)

    def post(self, message, alert_channel=False):

        if not self.initialised:
            return

        shout = '<!channel> => ' if alert_channel else ''

        try:
            text = f"{shout}{message}"

            _ = self.client.chat_postMessage(
                channel=self.channel,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    }
                ]
            )
        except SlackApiError as e:
            self.logger.error(f"Error sending slack message - {e}")
            if 'error' in e.response:
                self.logger.error(e.response["error"])

    def process_exception(self, e: Exception, msg):
        self.logger.exception(e)
        self.logger.error(msg)
        self.post(e, True)
        self.post(msg, True)

    def process_info(self, msg):
        self.logger.info(msg)
        self.post(msg, False)