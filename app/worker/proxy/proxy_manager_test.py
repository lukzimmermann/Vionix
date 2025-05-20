

from app.worker.proxy.proxy_manager import ProxyManager


p = ProxyManager()


for i in range(100):
    print(p.get_next_proxy())