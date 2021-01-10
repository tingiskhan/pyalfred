from typing import Dict, Any, TypeVar, Type
import requests


T = TypeVar("T", bound=requests.Request)


class BaseClient(object):
    def __init__(self, base_url: str, endpoint: str = ""):
        """
        Defines a base class for interfaces.
        :param base_url: The base address of the server
        :param endpoint: The endpoint of the server
        """

        self._base = base_url if not base_url.endswith("/") else base_url[:-1]

        if endpoint.startswith("/"):
            raise ValueError("The endpoint should not begin with a `/`!")

        self._ep = endpoint
        self._headers = {"Content-type": "application/json"}

    def url(self, endpoint: str = None):
        return f"{self._base}/{endpoint or self._ep}"

    def _make_request(self, meth, endpoint: str = None, req_type: Type[T] = requests.Request, **kwargs) -> T:
        return req_type(meth, url=self.url(endpoint), **kwargs)

    @staticmethod
    def _send_request(request: requests.Request, session: requests.Session = None) -> Dict[str, Any]:
        with (session or requests.Session()) as s:
            prepared = s.prepare_request(request)
            resp = s.send(prepared)

            if resp.status_code != 200:
                raise Exception(f"Got error code {resp.status_code}: {resp.text}")

            return resp.json()

    def add_header(self, key: str, value: str):
        self._headers[key] = value
        return self
