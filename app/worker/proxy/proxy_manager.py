import os
from dotenv import load_dotenv
from dataclasses import dataclass
from app.utils.singleton import singleton

load_dotenv()

@dataclass
class ProxyItem:
    ip: str
    port: str
    username: str
    password: str

@singleton
class ProxyManager():
    def __init__(self):
        self.__proxy_list_path__ = os.getenv('PROXY_LIST_PATH')
        
        with open(self.__proxy_list_path__, 'r') as file:
            self.proxies = [self.parse(line) for line in file.readlines()]

        self.current_index = -1


    def get_next_proxy(self) -> str:
        self.current_index += 1

        if self.current_index >= len(self.proxies):
            self.current_index = 0     

        proxy = self.proxies[self.current_index]

        if proxy.username and proxy.password:
            proxy_auth = f"{proxy.username}:{proxy.password}@"
        else:
            proxy_auth = ""

        return {
            "http": f"{proxy_auth}{proxy.ip}:{proxy.port}",
            "https": f"{proxy_auth}{proxy.ip}:{proxy.port}",
        }
    
    def parse(self, line: str) -> ProxyItem:
        elements = line.strip().split(':')

        if len(elements) == 4:
            return ProxyItem(elements[0], elements[1], elements[2], elements[3])
        elif len(elements) == 2:
            return ProxyItem(elements[0], elements[1], None, None)
        else:
            raise ValueError(f"Invalid proxy line format: {line}")
