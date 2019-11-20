import asyncio
import os
import uuid
import json
import datetime
import sys
import libdfx as dfx

from google.protobuf.json_format import ParseDict
from dfxsnippets.measurement_pb2 import SubscribeResultsRequest


class subscribeResults():
    def __init__(self, measurementID, token, websocketobj, num_chunks, out_folder=None):
        self.measurementID = measurementID
        self.token = token
        self.ws_url = websocketobj.ws_url
        self.num_chunks = num_chunks
        self.requestData = None
        self.ws_obj = websocketobj
        self.out_folder = out_folder
        self.subscribeResultsTime = 0

        if self.out_folder and not os.path.isdir(
                self.out_folder):  # Create directory if not there
            os.mkdir(self.out_folder)

    async def prepare_data(self):
        data = {}
        wsID = self.ws_obj.ws_ID
        requestID = uuid.uuid4().hex[:10]
        data['RequestID'] = requestID
        data['Query'] = {}
        data['Params'] = dict(ID=self.measurementID)

        websocketRouteID = '0510'
        requestMessageProto = ParseDict(data,
                                        SubscribeResultsRequest(),
                                        ignore_unknown_fields=True)
        self.requestData = f'{websocketRouteID:4}{wsID:10}'.encode(
        ) + requestMessageProto.SerializeToString()

    async def subscribe(self):
        print("Subscribing to results")
        await self.prepare_data()
        await self.ws_obj.handle_send(self.requestData )

        # Create a DFX Factory object
        self._dfxFactory = dfx.Factory()
        print("Created DFX Factory:", self._dfxFactory.getVersion())

        # Create an empty self._collector
        self._collector = None
        # Create collector
        self._collector = self._dfxFactory.createCollector()
        if self._collector.getCollectorState() == dfx.CollectorState.ERROR:
            print("Collector creation failed: {}".format(
                self._collector.getLastErrorMessage()))
            sys.exit(1)
        print("Created collector")

        counter = 0
        while counter < self.num_chunks:
            await self.ws_obj.handle_recieve()
            if counter == self.num_chunks - 1:
                subscribeResultsTime = datetime.datetime.now().time()
                self.subscribeResultsTime = subscribeResultsTime
                print("subscribeResultsTime - last chunk: ", subscribeResultsTime)
            if self.ws_obj.subscribeStats:
                response = self.ws_obj.subscribeStats[0]
                self.ws_obj.subscribeStats = []
                statusCode = response[10:13].decode('utf-8')
                if statusCode != '200':
                    print("Subscribe Status:", statusCode)

            elif self.ws_obj.chunks:
                counter += 1
                response = self.ws_obj.chunks[0]
                self.ws_obj.chunks = []
                print("Data received; Chunk: " + str(counter) + "; Status: " +
                      str(statusCode) + "; Time: " + str(datetime.datetime.now().time()))

                if self.out_folder:
                    with open(self.out_folder + '/result_' + str(counter) + '.bin', 'wb') as f:
                        f.write(response[13:])
                        print('/result_' + str(counter) + '.bin has been saved.')
                    decoded_data = self._collector.decodeMeasurementResult(response[13:])
                    print("decoded_data.getErrorCode():", decoded_data.getErrorCode())

        await self.ws_obj.handle_close()
        return


if __name__ == '__main__':
    measurementID = ''
    token = ''
    ws_url = ''
    out_folder = ''
    num_chunks = 2
    sub = subscribeResults(measurementID, token, ws_url, num_chunks, out_folder)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sub.subscribe())
