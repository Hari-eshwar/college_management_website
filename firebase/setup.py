"""Firebase setup helper — verifies connection and seeds initial data."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase import firebase_service


def main():
    ok = firebase_service.initialize()
    if not ok:
        print('[FAIL] Firebase not connected. Check FIREBASE_CONFIG_PATH and credentials file.')
        sys.exit(1)

    print('[OK] Firebase initialized successfully')

    # Verify database access
    test_data = firebase_service.get_data('attendance')
    if test_data is None:
        print('[INFO] No attendance data in Firebase yet (expected if first run)')
    else:
        print(f'[OK] Found attendance data in Firebase')

    # Seed a status marker
    firebase_service.save_data('_meta/setup', {
        'version': '1.0',
        'timestamp': os.popen('date +%Y-%m-%dT%H:%M:%S').read().strip()
    })
    print('[OK] Setup marker written to Firebase')

    # List existing collections
    students = firebase_service.get_data('students')
    if students:
        count = len(students) if isinstance(students, dict) else 1
        print(f'[OK] Found {count} students in Firebase')

    print()
    print('=== Firebase setup complete ===')
    print('Database :', os.getenv('FIREBASE_DATABASE_URL', '(not set)'))
    print('Storage  :', os.getenv('FIREBASE_STORAGE_BUCKET', '(not set)'))
    print()
    print('Place these rules in your Firebase console:')
    print('  Realtime Database → Rules : firebase/database.rules.json')
    print('  Storage → Rules           : firebase/storage.rules')


if __name__ == '__main__':
    main()
