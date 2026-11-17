"""Keep Windows from going to sleep while a render is writing files. This PC sleeps after half an hour
without a key press, and the full-quality render takes all night.

  python keep_awake.py "cache/film*hd*"

It holds the PC awake (the screen may still turn off) for as long as something matching the pattern has
changed in the last twenty minutes: a folder that got a new frame, the log. Then it ends by itself and the
PC's own sleep timer applies again. Nothing to switch back.
"""
import ctypes
import glob
import os
import sys
import time

ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)       # lasts as long as this process does
last = time.time()
while time.time() - last < 20 * 60:
    time.sleep(30)
    last = max(last, max((os.path.getmtime(p) for p in glob.glob(sys.argv[1])), default=0))
