from mss import MSS

with MSS() as sct:
    img = sct.grab(sct.monitors[1])

    print(type(img.rgb))
    print(len(img.rgb))
    print(img.rgb[:30])
    print(any(img.rgb))