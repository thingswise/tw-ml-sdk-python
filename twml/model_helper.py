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

import numpy as np

class Filter:

    def __call__(self, v):
        return self.filter(v)

    def __add__(self, x):
        return AndFilter(self, x)

class AndFilter(Filter):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def filter(self, v):
        return a(v) and b(v)

class HasCoord(Filter):

    def __init__(self, coord):
        self.coord = coord

    def filter(self, v):
        return self.coord in v.coordinates

class ModelHelper:

    def __init__(self):
        pass


class TimeseriesFeatureExtractor:

    def __init__(self, window, step, coord):
        self.window = window
        self.step = step
        self.coord = coord

    def __call__(self, src):
        ts = sorted(src.timeseries(self.coord), key=lambda x: x.ts)
        l = len(ts)
        if l > 0:
            end = ts[-1].ts + 1
            start = ts[0].ts
            S = (end - start - self.window) // self.step + 1
            for i in xrange(0, S):
                q = end - i*self.step
                p = end - i*self.step - self.window
                sub = [ v for v in ts if v.ts >= p and v.ts < q ]
                yield self.extract(sub)

class TimeseriesFeatureCoordinateExtractor(TimeseriesFeatureExtractor):

    def __init__(self, window, step, coord, coordExtractor):
        TimeseriesFeatureExtractor.__init__(self, window, step, coord)
        self.coordExtractor = coordExtractor

    def extract(self, sub):
        return { k:self.coordExtractor[k](sub) for k in self.coordExtractor }

class OnTimeExtractor:

    def __call__(self, sub):
        s = 0
        for i in xrange(len(sub)-1):
            v1 = 1 if sub[i].value > 0 else 0
            v2 = 1 if sub[i+1].value > 0 else 0
            t = sub[i+1].ts - sub[i].ts
            s += (v1+v2)/2 * t
        return s

class StopsExtractor:

    def __call__(self, sub):
        s = 0
        for i in xrange(len(sub)-1):
            v1 = 1 if sub[i].value > 0 else 0
            v2 = 1 if sub[i+1].value > 0 else 0
            if v2 == 0 and v1 > 0:
                s += 1
        return s

class Scale:
        
    def __init__(self, scale, ext):
        self.scale = scale
        self.ext = ext
        
    def __call__(self, sub):
        return self.scale * self.ext(sub)
        
class Sum:
    
    def __call__(self, sub):
        s = 0
        for d in sub:
            s += d.value
        return s
    
class TimeseriesCollectionFeatureExtractor:
    
    def __init__(self, _from, _to, window, step, coords):
        self._from = _from
        self._to = _to
        self.window = window
        self.step = step
        self.coords = coords            
    
    def __call__(self, src):
        end = self._to
        start = self._from
        S = (end - start) // self.step
        for i in xrange(0, S):
            q = start + (i+1) * self.step
            p = start + i * self.step
            r = {}
            for c in self.coords:
                sub = [ v for v in src.timeseries(c) if v.ts >= p and v.ts < q ]
                m = self.extract(c, sub)
                for k, v in m.iteritems():
                    if k in r:
                        raise ValueError("Coordinate %s has already been set" % k)
                    r[k] = v
            yield r        

class TimeseriesCollectionFeatureCoordinateExtractor(TimeseriesCollectionFeatureExtractor):

    def __init__(self, _from, _to, window, step, coordExtractor):
        TimeseriesCollectionFeatureExtractor.__init__(self, _from, _to, window, step, list(coordExtractor.keys()))
        self.coordExtractor = coordExtractor

    def extract(self, coord, sub):
        return { k: self.coordExtractor[coord][k](sub) for k in self.coordExtractor[coord] }

class Extract:

    def __init__(self, extractor):
        self.extractor = extractor

    def __call__(self, vectors):
        for v in vectors:
            for x in self.extractor(v):
                yield x

class Progress:

    def __init__(self, label=""):
        self.label = label

    def __call__(self, n, total):
        if n % 10 == 0 or n == total:
            print "%s%d/%d" % ("%s " % self.label if self.label else "", n, total)

def diag_vect(v):
    while True:
        yield v
        
def matrix(*argv):
    N = 0 # cols
    M = -1 # rows
    for v in argv:
        N += 1
        try:
            M = max(M, len(v))
        except TypeError:
            continue
    if N == 0:
        raise ValueError("No vectors provided")
    if M < 0:
        raise ValueError("Cannot determine matrix dimensions")
    arr = np.zeros((M, N))
    for j, v in enumerate(argv):
        p = 0
        try:
            l = len(v)
        except TypeError:
            for i in xrange(M):
                arr[i, j] = next(v, 0)
            continue
        for i in xrange(len(v)):
            arr[i, j] = v[i]
            p += 1  
    return np.mat(arr)

def stack(*argv):
    N = -1
    M = 0
    for v in argv:
        if len(v.shape) != 2:
            raise ValueError
        if N == -1:
            N = v.shape[1]
        else:
            if N != v.shape[1]:
                raise ValueError("All matrices must have the same number of columns")
        M += v.shape[0]
    arr = np.zeros((M, N))
    i = 0
    for v in argv:
        for k in xrange(v.shape[0]):
            for j in xrange(N):
                arr[i, j] = v[k, j]
            i += 1
    return np.mat(arr)
            
class VectorList:
    
    def __init__(self, values):
        self.values = list(values)
        
    def __getitem__(self, key):
        return [ v[key] for v in self.values ]
    
    def __len__(self):
        return len(self.values)
    
    def __iter__(self):
        return self.values.__iter__()
            