from twilio.rest import Client
from backend.config import settings
from backend.utils.logger import logger

class TwilioNotifier:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def send_message(self, to, body):
        try:
            message = self.client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to
            )
            logger.info(f"Message sent to {to}: {message.sid}")
        except Exception as e:
            logger.error(f"Twilio error: {e}")

notifier = TwilioNotifier()
