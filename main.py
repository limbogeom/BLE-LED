import asyncio, signal, sys
from bleak import BleakClient, BleakScanner
from mss import mss

DEVICE_PREFIX = "ELK-BLEDOB"
WRITE_UUIDS = ["0000fff3-0000-1000-8000-00805f9b34fb"]
FPS = 10
SMOOTHING = 0.2
DEFAULT_GAMMA = 0.8

# ------- LUT GAMMA -------
def create_lut(gamma): return [int((i/255)**gamma*255) for i in range(256)]
LUT = create_lut(DEFAULT_GAMMA)
def apply_gamma(v): return LUT[v]

# ------- PACK BYTES -------
def pack_init(): return bytes.fromhex("7e0600830f200c0600ef")
def pack_color(r,g,b): return bytes([0x7e,0x07,0x05,0x03,r,g,b,0x10,0xef])

# ------- SCREEN SAMPLE -------
def sample_screen():
    try:
        with mss() as sct:
            img = sct.grab(sct.monitors[1])
            n = len(img.pixels)//4
            r = sum(img.pixels[i] for i in range(0,len(img.pixels),4))//n
            g = sum(img.pixels[i] for i in range(1,len(img.pixels),4))//n
            b = sum(img.pixels[i] for i in range(2,len(img.pixels),4))//n
            return apply_gamma(r), apply_gamma(g), apply_gamma(b)
    except: return 0,0,0

# ------- BLE HELP -------
async def find_char(client):
    svcs = await client.get_services()
    writable=[]
    for s in svcs:
        for c in s.characteristics:
            if "write" in c.properties or "write-without-response" in c.properties: writable.append(c.uuid)
    for u in WRITE_UUIDS: 
        if u in writable: return u
    return writable[0] if writable else None

# ------- MAIN LOOP -------
async def run_loop(address):
    async with BleakClient(address) as client:
        if not client.is_connected: return
        char = await find_char(client)
        if not char: return
        await client.write_gatt_char(char, pack_init(), response=False)
        prev=[0,0,0]; interval=max(0.02,1/FPS)
        stop=False
        signal.signal(signal.SIGINT, lambda s,f: setattr(sys.modules[__name__],"stop",True))
        while not stop:
            r,g,b=sample_screen()
            for i,v in enumerate([r,g,b]): prev[i]=SMOOTHING*prev[i]+(1-SMOOTHING)*v
            rr,gg,bb=int(prev[0]),int(prev[1]),int(prev[2])
            try: await client.write_gatt_char(char, pack_color(rr,gg,bb), response=False)
            except: pass
            await asyncio.sleep(interval)
        await client.write_gatt_char(char, pack_color(0,0,0), response=False)

# ------- DISCOVERY -------
async def discover_device():
    print("Discovering devices...")
    devs = await BleakScanner.discover(timeout=5)
    for d in devs:
        if d.name and d.name.startswith(DEVICE_PREFIX): return d.address
    print("Devices not found")
    return None

# ------- ENTRY POINT -------
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma",type=float,default=DEFAULT_GAMMA)
    args=parser.parse_args()
    LUT=create_lut(args.gamma)
    addr=asyncio.run(discover_device())
    if addr: asyncio.run(run_loop(addr))
