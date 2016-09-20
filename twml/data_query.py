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
from __future__ import division

class DataPoint:

    def __init__(self, ts, value):
        self.ts = ts
        self.value = value

    def __repr__(self):
        return "(%d, %.2f)" % (self.ts, self.value)

class Vector:

    def __init__(self, key, coordinates):
        self.key = key
        self.coordinates = coordinates

    def __repr__(self):
        return "Vector(key=%s, coordinates=%s)" % (self.key, self.coordinates)

    def timeseries(self, key):
        return self.coordinates[key]

class DataQuery:

    def __init__(self, qapi_url, templates, period, interval, _from, _to, key,
            input_data=[], input_data_len=0, split=None, progress=None, aggregation="avg"):
        self.qapi_url = qapi_url
        self.templates = templates
        self.period = period
        self.interval = interval
        self._from = _from
        self._to = _to
        self.input_data = input_data
        self.input_data_len = input_data_len
        self.key = key
        self.split = split
        self.progress = progress
        self.aggregation = aggregation

    def get(self):
        import requests
        import time

        #print "%.2f" % time.time()

        if self._from <= 0:
            _from = int(time.time()) + self._from
        else:
            _from = self._from

        if self._to <= 0:
            _to = int(time.time()) + self._to
        else:
            _to = self._to

        time_span = _to - _from
        if time_span <= 0:
            raise ValueError("Invalid to and from boundaries")

        if self.interval <= 0:
            raise ValueError("Invalid interval")

        total = self.input_data_len * (time_span // self.interval) * len(self.templates)
        cnt = 0

        for d in self.input_data.get() if hasattr(self.input_data, "get") else self.input_data:
            start = _to - self.interval
            while start >= _from:
                end = start + self.interval

                coordinates = {}
                for template_key in self.templates:
                    template = self.templates[template_key]
                    url = "%s/timeseries/%s" % (self.qapi_url, template(d))
                    r = requests.get(
                        url,
                        params={
                            "from": start,
                            "to": end,
                            "period": self.period
                        })
                    if r.status_code != 200:
                        raise ValueError("Data Query returned error: %d" % r.status_code)
                    cnt += 1
                    if self.progress:
                        self.progress(cnt, total)
                    timeseries = []
                    for p in r.json():
                        ts = int(p["name"])
                        _sum = p["value"]["sum"]
                        _cnt = p["value"]["cnt"]
                        _stddev = p["value"]["stddev"]
                        _max = p["value"]["max"]
                        _min = p["value"]["min"]
                        if self.aggregation == "avg" or self.aggregation == "val":                            
                            if _cnt > 0:
                                _avg = _sum / _cnt
                                timeseries.append(DataPoint(ts, _avg))
                            else:
                                timeseries.append(DataPoint(ts, 0))
                        elif self.aggregation == "sum":
                            timeseries.append(DataPoint(ts, _sum))
                        elif self.aggregation == "stddev":
                            timeseries.append(DataPoint(ts, _stddev))
                        elif self.aggregation == "min":
                            timeseries.append(DataPoint(ts, _min))
                        elif self.aggregation == "max":
                            timeseries.append(DataPoint(ts, _max))
                        elif self.aggregation == "cnt":
                            timeseries.append(DataPoint(ts, _cnt))
                        else:
                            raise ValueError("Unsupported aggregation: %s" + self.aggregation)                            
                            
                    coordinates[template_key] = timeseries

                if self.split is None:
                    vector = Vector(key="%s:%d" % (self.key(d), start), coordinates=coordinates)
                    yield vector
                    start = start - self.interval
                else:
                    for template_key in coordinates:
                        for p in self.split(coordinates[template_key]):
                            vector = Vector(key="%s:%d:%s" % (self.key(d), start, template_key),
                                            coordinates={template_key: p})
                            yield vector
                    start = start - self.interval