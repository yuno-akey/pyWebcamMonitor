import ssl
import smtplib
import requests
from camutils import CAMCONF
from enum import Enum, auto
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from requests.exceptions import RequestException


class STATUS(Enum):
    WAITING = auto()
    THROTTLED = auto()
        
        
# AbstractNotifierModel
    
class NotifierModel(ABC):
    
    @abstractmethod
    def initialize_notifier(self):
        pass
    
    @abstractmethod
    def process_notification(self, message):
        pass
    
    @abstractmethod
    def set_notifier_status_waiting(self):
        pass
    
    @abstractmethod
    def set_notifier_status_throttled(self):
        pass
    
    @abstractmethod
    def notify_to_admin(self, message):
        pass
    
    @abstractmethod
    def close_notifier(self):
        pass


# LineNotifier
    
class LineNotifier(NotifierModel):
    def __init__(self):
        self.token = CAMCONF.LINE_TOKEN.value
        self.api_url = "https://notify-api.line.me/api/notify"
        self.status = STATUS.WAITING
        
    def initialize_notifier(self):
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def process_notification(self, message):
        self.payload = {"message": message}
        
    def set_notifier_status_waiting(self):
        self.status = STATUS.WAITING
            
    def set_notifier_status_throttled(self):
        self.status = STATUS.THROTTLED
        
    def notify_to_admin(self):
        response = requests.post(self.api_url, headers=self.headers, data=self.payload)
        if response.status_code == 200:
            self.set_notifier_status_throttled()
        else:
            raise RequestException(f"Failed to send notification: {response.text}")
        
    def close_notifier(self):
        pass
        
        
# EmailNotiifier
    
class EmailNotifier(NotifierModel):
    def __init__(self):
        self.smtp_server = CAMCONF.SMTP_SERVER.value
        self.smtp_port = CAMCONF.SMTP_PORT.value
        self.notifier_email = CAMCONF.NOTIFIER_EMAIL.value
        self.notifier_password = CAMCONF.NOTIFIER_PASSWORD.value
        self.admin_email = CAMCONF.ADMIN_EMAIL.value
        self.ssl_context = ssl.create_default_context()
        self.status = STATUS.WAITING

    def initialize_notifier(self):
        self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        self.server_reply = None
        self.server_reply = self.server.ehlo()
        print(self.server_reply)
        self.server.starttls(context=self.ssl_context)
        self.server_reply = self.server.ehlo()
        print(self.server_reply)
        self.server.login(self.notifier_email, self.notifier_password)
        
    def process_notification(self, message):
        self.message = MIMEMultipart()
        self.message["From"] = self.notifier_email
        self.message["To"] = self.admin_email
        self.message["Subject"] = message
        self.message.attach(MIMEText(message, "plain"))
    
    def set_notifier_status_waiting(self):
        self.status = STATUS.WAITING
    
    def set_notifier_status_throttled(self):
        self.status = STATUS.THROTTLED
        
    def notify_to_admin(self):
        self.server.sendmail(self.notifier_email, self.admin_email, self.message.as_string())
        self.set_notifier_status_throttled()
    
    def close_notifier(self):
        self.server.quit()