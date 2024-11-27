import asyncio
from enum import Enum
from ssl import SSLContext
from http import HTTPStatus

# Some of the imports are deprecated in the newer python versions
# But we still have support for 3.8 where collection.abc didn't have
# proper types yet.
from typing import Final, Optional, Mapping, Iterable, Tuple, Callable, Union
from multidict import CIMultiDict


PICOWS_DEBUG_LL: Final = 9
WSHeadersLike = Union[Mapping[str, str], Iterable[Tuple[str, str]]]
WSServerListenerFactory = Callable[[WSUpgradeRequest], Union[WSListener, WSUpgradeResponseWithListener, None]]
WSBuffer = Union[bytes, bytearray, memoryview]


class WSError(RuntimeError): ...


class WSMsgType(Enum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    PING = 0x9
    PONG = 0xA
    CLOSE = 0x8


class WSCloseCode(Enum):
    NO_INFO = 0
    OK = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    ABNORMAL_CLOSURE = 1006
    INVALID_TEXT = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014


class WSAutoPingStrategy(Enum):
    PING_WHEN_IDLE = 1
    PING_PERIODICALLY = 2


class WSFrame:
    @property
    def tail_size(self) -> int: ...

    @property
    def msg_type(self) -> WSMsgType: ...

    @property
    def fin(self) -> bool: ...

    @property
    def rsv1(self) -> bool: ...

    @property
    def last_in_buffer(self) -> bool: ...

    def get_payload_as_bytes(self) -> bytes: ...
    def get_payload_as_utf8_text(self) -> str: ...
    def get_payload_as_ascii_text(self) -> str: ...
    def get_payload_as_memoryview(self) -> memoryview: ...
    def get_close_code(self) -> WSCloseCode: ...
    def get_close_message(self) -> bytes: ...
    def __str__(self): ...


class WSTransport:
    @property
    def underlying_transport(self) -> asyncio.Transport: ...

    @property
    def is_client_side(self) -> bool: ...

    @property
    def is_secure(self) -> bool: ...

    @property
    def request(self) -> WSUpgradeRequest: ...

    @property
    def response(self) -> WSUpgradeResponse: ...

    def send(
        self,
        msg_type: WSMsgType,
        message: Optional[WSBuffer],
        fin: bool = True,
        rsv1: bool = False,
    ): ...
    def send_ping(self, message: Optional[WSBuffer]=None): ...
    def send_pong(self, message: Optional[WSBuffer]=None): ...
    def send_close(self, close_code: WSCloseCode = ..., close_message: Optional[WSBuffer]=None): ...
    def disconnect(self, graceful: bool = True): ...
    async def wait_disconnected(self): ...
    async def measure_roundtrip_time(self, rounds: int) -> list[float]: ...
    def notify_user_specific_pong_received(self): ...


class WSListener:
    def on_ws_connected(self, transport: WSTransport): ...
    def on_ws_frame(self, transport: WSTransport, frame: WSFrame): ...
    def on_ws_disconnected(self, transport: WSTransport): ...
    def send_user_specific_ping(self, transport: WSTransport): ...
    def is_user_specific_pong(self, frame: WSFrame): ...
    def pause_writing(self): ...
    def resume_writing(self): ...


class WSUpgradeRequest:
    @property
    def method(self) -> bytes: ...

    @property
    def path(self) -> bytes: ...

    @property
    def version(self) -> bytes: ...

    @property
    def headers(self) -> CIMultiDict: ...


class WSUpgradeResponse:
    @staticmethod
    def create_error_response(status: Union[int, HTTPStatus], body=None, extra_headers: Optional[WSHeadersLike]=None): ...

    @staticmethod
    def create_101_response(extra_headers: Optional[WSHeadersLike]=None): ...

    @property
    def version(self) -> bytes: ...

    @property
    def status(self) -> HTTPStatus: ...

    @property
    def headers(self) -> CIMultiDict: ...


class WSUpgradeResponseWithListener:
    def __init__(self, response: WSUpgradeResponse, listener: Optional[WSListener]): ...


async def ws_connect(
    ws_listener_factory: Callable[[], WSListener],
    url: str,
    *,
    ssl_context: Union[SSLContext, None] = None,
    disconnect_on_exception: bool = True,
    websocket_handshake_timeout=5,
    logger_name: str = "client",
    enable_auto_ping: bool = False,
    auto_ping_idle_timeout: float = 10,
    auto_ping_reply_timeout: float = 10,
    auto_ping_strategy: WSAutoPingStrategy = ...,
    enable_auto_pong: bool = True,
    extra_headers: Optional[WSHeadersLike] = None,
    **kwargs,
) -> Tuple[WSTransport, WSListener]: ...


async def ws_create_server(
    ws_listener_factory: WSServerListenerFactory,
    host: Union[str, Iterable[str], None] = None,
    port: Union[int, None] = None,
    *,
    disconnect_on_exception: bool = True,
    websocket_handshake_timeout: int = 5,
    logger_name: str = "server",
    enable_auto_ping: bool = False,
    auto_ping_idle_timeout: float = 20,
    auto_ping_reply_timeout: float = 20,
    auto_ping_strategy: WSAutoPingStrategy = ...,
    enable_auto_pong: bool = True,
    **kwargs,
) -> asyncio.Server: ...