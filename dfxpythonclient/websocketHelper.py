import asyncio
import json
import uuid
import websockets


class WebsocketHandler():
    def __init__(self, token, websocket_url):
        self.token = token
        self.ws_url = websocket_url
        self.headers = dict(Authorization="Bearer {}".format(self.token))
        self.ws = None
        self.ws_ID = uuid.uuid4().hex[:10]      # Use same ws_ID for all connections

        # Use this to form a mutual exclusion lock
        self.recv = True

        # Lists for tracking return values
        self.addDataStats = []
        self.subscribeStats = []
        self.chunks = []
        self.unknown = {}        # For storing messages not coming from a known websocket sender

    async def connect_ws(self):
        self.ws = await self.handle_connect()

    async def handle_connect(self):
        try:
            ws = await websockets.client.connect(self.ws_url, extra_headers=self.headers)
        except:
            raise Exception("Cannot connect to websocket")
        print(" Websocket Connected ")
        return ws

    async def handle_close(self):
        print(" Closing Websocket ")
        await self.ws.close()
        return

    async def handle_send(self, content):
        if self.ws == None:
            await asyncio.sleep(0.5)    # Wait for websocket to connect
        await self.ws.send(content)

    async def handle_recieve(self):
        if self.recv == True:
            # Mutual exclusion lock; prevents multiple calls of recv() on the same websocket connection
            self.recv = False
            response = await self.ws.recv()
            self.recv = True
        else:
            return
        if response:
            wsID = response[0:10].decode('utf-8')
            # Sort out response messages by type
            if wsID != self.ws_ID:
                #print("Received a package that didn't come from a local sender")
                self.unknown[wsID] = response

            with open('./default.config') as json_file:  
                data = json.load(json_file)
            
                if len(response) == int(data["Subscribe_status"]):
                    self.subscribeStats.append(response)
                elif len(response) <= int(data["Adddata_status"]):
                    self.addDataStats.append(response)
                else:
                    self.chunks.append(response)
        return
