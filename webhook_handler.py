"""Helper class to handle webhook callbacks from node-sonos-http-api and various REST commands."""
import copy
from distutils.util import strtobool

from aiohttp import web


class SonosWebhook:
    def __init__(self, display, sonos_data, callback):
        """Initialize the webhook handler."""
        self.callback = callback
        self.display = display
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
                web.post("/show-detail", self.show_detail),
            ]
        )
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8080)
        await site.start()

    async def get_status(self, request):
        """Report the status of the application."""
        payload = copy.copy(vars(self.sonos_data))
        payload.pop("session")
        return web.json_response(payload)

    async def set_room(self, request):
        """Set the monitored room."""
        payload = await request.post()
        room = payload.get("room")
        self.sonos_data.set_room(room)
        return web.Response(text="OK")

    async def show_detail(self, request):
        """Set the monitored room."""
        if not self.sonos_data.is_playing():
            return web.HTTPBadRequest(reason="Not playing")

        payload = await request.post()
        detail = payload.get("detail")
        if not detail:
            return web.HTTPBadRequest(reason="Parameter 'detail' must be provided")

        detail = strtobool(detail)
        timeout = payload.get("timeout")
        if timeout:
            timeout = int(timeout)
        self.display.show_album(detail, timeout)
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
