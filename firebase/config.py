import os
import json
import firebase_admin
from firebase_admin import credentials, auth, db as firebase_db, storage, messaging
from datetime import datetime, timezone

FIREBASE_CONFIG_PATH = os.getenv('FIREBASE_CONFIG_PATH', 'firebase/serviceAccountKey.json')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')
FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET', '')

class FirebaseService:
    def __init__(self):
        self.app = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return True
        try:
            if os.path.exists(FIREBASE_CONFIG_PATH):
                cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
                options = {}
                if FIREBASE_DATABASE_URL:
                    options['databaseURL'] = FIREBASE_DATABASE_URL
                if FIREBASE_STORAGE_BUCKET:
                    options['storageBucket'] = FIREBASE_STORAGE_BUCKET
                self.app = firebase_admin.initialize_app(cred, options)
                self._initialized = True
                return True
            else:
                return False
        except Exception:
            return False

    def create_user(self, email, password, display_name=None):
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            return user.uid
        except Exception:
            return None

    def verify_token(self, id_token):
        try:
            decoded = auth.verify_id_token(id_token)
            return decoded
        except Exception:
            return None

    def send_notification(self, token, title, body):
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=token
            )
            response = messaging.send(message)
            return response
        except Exception:
            return None

    def send_topic_notification(self, topic, title, body):
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                topic=topic
            )
            response = messaging.send(message)
            return response
        except Exception:
            return None

    def save_data(self, path, data):
        if not self._initialized:
            return False
        try:
            ref = firebase_db.reference(path)
            ref.set(data)
            return True
        except Exception:
            return False

    def get_data(self, path):
        if not self._initialized:
            return None
        try:
            ref = firebase_db.reference(path)
            return ref.get()
        except Exception:
            return None

    def upload_file(self, local_path, remote_path):
        if not self._initialized:
            return None
        try:
            bucket = storage.bucket()
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            blob.make_public()
            return blob.public_url
        except Exception:
            return None

    def sync_attendance_to_firebase(self, attendance_record):
        if not self._initialized:
            return False
        try:
            data = {
                'student_id': attendance_record.student_id,
                'faculty_id': attendance_record.faculty_id,
                'subject_name': attendance_record.subject_name,
                'date': attendance_record.date.isoformat(),
                'time': attendance_record.time,

                'status': attendance_record.status,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            path = f'attendance/{attendance_record.date}/{attendance_record.student_id}'
            self.save_data(path, data)
            return True
        except Exception:
            return False
