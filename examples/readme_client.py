import asyncio
import uvloop
from picows import WSFrame, WSTransport, WSListener, ws_connect, WSMsgType


class ClientListener(WSListener):
    def on_ws_connected(self, transport: WSTransport):
        self.transport = transport
        transport.send(WSMsgType.TEXT, b"Hello world")

    def on_ws_frame(self, transport: WSTransport, frame: WSFrame):
        print(f"Echo reply: {frame.get_payload_as_ascii_text()}")
        transport.disconnect()


async def main(url):
    (_, client) = await ws_connect(ClientListener, url)
    await client.transport.wait_disconnected()


if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main("ws://127.0.0.1:9001"))