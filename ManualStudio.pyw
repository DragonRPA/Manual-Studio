import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from manual_capture_studio import main

if __name__ == '__main__':
    main()
