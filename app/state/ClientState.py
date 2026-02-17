import app.resp as resp


class ClientState:
    def __init__(self):
        self.is_multi = False
        self.multi_queue = []

    def queue_command(self, func, args):
        self.multi_queue.append((func, args))
        return resp.encode_simple_str("QUEUED")
