from __future__ import annotations

import asyncio
from typing import Optional

from bleak import BleakClient, BleakScanner

from ble_led.config import (
    DEVICE_PREFIX,
    DISCOVERY_TIMEOUT,
    WRITE_UUIDS,
    WRITE_WITH_RESPONSE,
)

import logging

logger = logging.getLogger("ble-led")

class BLEController:

    def __init__(self, device_prefix: str = DEVICE_PREFIX, timeout: int = DISCOVERY_TIMEOUT):
        self.device_prefix = device_prefix
        self.timeout = timeout

        self.address: Optional[str] = None
        self.client: Optional[BleakClient] = None
        self.characteristic: Optional[str] = None

    async def discover(self) -> Optional[str]:

        logger.info("Scanning for BLE devices...")

        devices = await BleakScanner.discover(timeout=self.timeout)

        for device in devices:

            if device.name and device.name.startswith(self.device_prefix):

                self.address = device.address
                logger.info("Found: %s", self.address)
                return self.address
            
    async def connect(self):

        if self.address is None:
            raise RuntimeError("Device has not been discovered.")
        
        self.client = BleakClient(self.address)

        await self.client.connect()

        if not self.client.is_connected:
            raise RuntimeError("Failed to connect.")
        
        logger.info("Connected")
        
        self.characteristic = await self.find_characteristic()

    async def disconnect(self):

        if self.client is not None:
            await self.client.disconnect()
            logger.info("Disconnected")

    async def find_characteristic(self) -> str:
        services = self.client.services

        writable = []

        for service in services:

            for char in service.characteristics:
                if "write" in char.properties or "write-without-response" in char.properties:
                    writable.append(char.uuid)

        for uuid in WRITE_UUIDS:

            if uuid in writable:
                logger.debug("Characteristic found: %s", uuid)
                return uuid
            
        if writable:
            logger.debug("Characteristic found: %s", writable[0])
            return writable[0]
        
        raise RuntimeError("No writable characteristic found.")
    
    async def write(self, packet: bytes):
        if self.client is None:
            raise RuntimeError("Not connected.")
        
        await self.client.write_gatt_char(
            self.characteristic,
            packet,
            response=WRITE_WITH_RESPONSE
        )
        logger.debug("Writing %s", packet.hex())

    async def reconnect(self):
        await self.disconnect()

        await asyncio.sleep(1)

        await self.connect()