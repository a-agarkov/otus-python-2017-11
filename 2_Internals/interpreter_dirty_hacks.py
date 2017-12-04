import sys
sys._getframe(1)

def bleh(frameint):
    frame = sys._getframe(frameint)
    print(frame)
    return frame

sys._getframe(1)
bleh(0).f_locals['frame']