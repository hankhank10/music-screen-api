"""Helper class to handle webhook callbacks from node-sonos-http-api."""
from aiohttp import web


class SonosWebhook():

    def __init__(self, sonos_data, callback):
        """Initialize the webhook handler."""
        self.callback = callback
        self.runner = None
        self.sonos_data = sonos_data

    async def listen(self):
        """Start listening server."""
        server = web.Server(self.handle)
        self.runner = web.ServerRunner(server)
        await self.runner.setup()
        site = web.TCPSite(self.runner, 'localhost', 8080)
        await site.start()

    async def handle(self, request):
        """Handle a webhook received from node-sonos-http-api."""
        json = await request.json()
        if json['type'] == 'transport-state':
            if json['data']['roomName'] == self.sonos_data.room:
                await self.sonos_data.refresh(json['data']['state'])
                await self.callback()
        return web.Response(text="hello")

    async def stop(self):
        """Stop the listening server."""
        if self.runner:
            await self.runner.cleanup()
