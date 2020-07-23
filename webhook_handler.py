"""Helper class to handle webhook callbacks from node-sonos-http-api and various REST commands."""
from aiohttp import web

STATUS_ATTRIBUTES = [
    "room",
    "status",
    "trackname",
    "artist",
    "album",
    "duration",
    "last_poll",
    "last_webhook",
    "webhook_active",
]


class SonosWebhook:
    def __init__(self, sonos_data, callback):
        """Initialize the webhook handler."""
        self.callback = callback
        self.runner = None
        self.sonos_data = sonos_data

    async def listen(self):
        """Start listening server."""
        app = web.Application()
        app.add_routes(
            [
                web.post("/", self.handle_webhook),
                web.get("/status", self.get_status),
                web.post("/set-room", self.set_room),
            ]
        )
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8080)
        await site.start()

    async def get_status(self, request):
        """Report the status of the application."""
        payload = {}
        for attr in STATUS_ATTRIBUTES:
            payload[attr] = getattr(self.sonos_data, attr)
        return web.json_response(payload)

    async def set_room(self, request):
        """Set the monitored room."""
        payload = await request.post()
        room = payload.get("room")
        self.sonos_data.set_room(room)
        return web.Response(text="OK")

    async def handle_webhook(self, request):
        """Handle a webhook received from node-sonos-http-api."""
        json = await request.json()
        if json["type"] == "transport-state":
            if json["data"]["roomName"] == self.sonos_data.room:
                await self.sonos_data.refresh(json["data"]["state"])
                await self.callback()
        return web.Response(text="OK")

    async def stop(self):
        """Stop the listening server."""
        if self.runner:
            await self.runner.cleanup()
