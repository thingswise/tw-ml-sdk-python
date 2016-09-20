# Copyright 2016 Thingswise, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
class MetadataQuery:

    def __init__(self, jets_url, input_data=[], progress=None):
        self.jets_url = jets_url
        self.progress = progress
        self.input_data = input_data

    def get(self, batch_size=30):
        import requests

        cnt = 0
        batch_size = 1 # Override batch size for now
        batch = []
        for d in self.input_data:
            batch.append(d)
            if len(batch) >= batch_size:
                # r = requests.post(self.jets_url, json=batch)
                r = requests.get(self.jets_url, params={ "deviceId": batch[0] })
                batch = []
                if r.status_code != 200:
                    raise ValueError("Metadata Query returned error: %d" % r.status_code)
                for v in r.json():
                    cnt += 1
                    if self.progress:
                        self.progress(cnt, len(self.input_data))
                    yield v
        if len(batch) > 0:
            # r = requests.post(self.jets_url, json=batch)
            r = requests.get(self.jets_url, params={ "deviceId": batch[0] })
            if r.status_code != 200:
                raise ValueError("Metadata Query returned error: %d" % r.status_code)
            for v in r.json():
                cnt += 1
                if self.progress:
                    self.progress(cnt, len(self.input_data))
                yield v