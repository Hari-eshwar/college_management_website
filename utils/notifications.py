import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail as SGmail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    from vonage_sms import Sms as VonageSms
    from vonage import Auth as VonageAuth
    VONAGE_AVAILABLE = True
except ImportError:
    VONAGE_AVAILABLE = False


class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SMTP_EMAIL', '')
        self.sender_password = os.getenv('SMTP_PASSWORD', '')
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')
        self.twilio_sid = os.getenv('TWILIO_SID', '')
        self.twilio_token = os.getenv('TWILIO_TOKEN', '')
        self.twilio_from = os.getenv('TWILIO_FROM', '')
        self.vonage_api_key = os.getenv('VONAGE_API_KEY', '')
        self.vonage_api_secret = os.getenv('VONAGE_API_SECRET', '')
        self.vonage_from = os.getenv('VONAGE_FROM', 'SmartAT')

    def send_email(self, to_email, subject, body):
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            try:
                message = SGmail(
                    from_email=self.sender_email or 'noreply@smartattendance.com',
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=body,
                )
                sg = SendGridAPIClient(self.sendgrid_api_key)
                sg.send(message)
                return True
            except Exception:
                pass
        if not self.sender_email or not self.sender_password:
            return False
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception:
            return False

    def send_sms(self, to_phone, message):
        if VONAGE_AVAILABLE and self.vonage_api_key and self.vonage_api_secret:
            try:
                client = VonageSms(VonageAuth(self.vonage_api_key, self.vonage_api_secret))
                client.send_message({'from': self.vonage_from, 'to': to_phone, 'text': message})
                return True
            except Exception:
                pass
        if not self.twilio_sid or not self.twilio_token or not self.twilio_from:
            return False
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            client.messages.create(body=message, from_=self.twilio_from, to=to_phone)
            return True
        except Exception:
            return False

    def send_parent_absence_alert(self, student_name, parent_email, subject, date):
        subject_line = f'Attendance Alert: {student_name} was absent'
        body = f'''
Dear Parent,

This is to inform you that {student_name} was marked ABSENT for {subject} on {date}.

Please ensure regular attendance.

Regards,
Smart Attendance System
'''
        return self.send_email(parent_email, subject_line, body)

    def send_leave_status_notification(self, faculty_email, faculty_name, status, admin_remarks=''):
        subject_line = f'Leave Request {status}'
        body = f'''
Dear {faculty_name},

Your leave request has been {status}.

{admin_remarks}

Regards,
Smart Attendance System
'''
        return self.send_email(faculty_email, subject_line, body)

    def send_parent_sms_alert(self, parent_phone, student_name, message_type, details=''):
        messages = {
            'absent': f'Smart Attendance: {student_name} was marked ABSENT today. Please ensure regular attendance.',

        }
        msg = messages.get(message_type, f'Smart Attendance: {student_name} - {details}')
        return self.send_sms(parent_phone, msg)