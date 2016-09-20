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
keydefs = {}

class KeyDef:

    def __init__(self, keydef):
        self.d = KeyDef.parse_def(keydef)

    @staticmethod
    def parse_def(d):
        result = []
        i = d.find("{")
        s = 0
        while i != -1:
            result.append(d[s:i])
            j = d.find("}", i+1)
            if j == -1:
                raise ValueError("Invalid key def: %s" % d)
            else:
                n = d[i+1:j]
                result.append(n)
                s = j+1
                i = d.find("{", s)
        result.append(d[s:])
        return result

    @staticmethod
    def get(d):
        global keydefs
        try:
            return keydefs[d]
        except KeyError:
            keydefs[d] = KeyDef(d)
            return keydefs[d]

    def apply(self, r):
        result = ""
        for i in range(len(self.d)):
            if i % 2 == 0:
                s = self.d[i]
            else:
                s = r(self.d[i])
            if type(s) == unicode:
                s = s.encode("utf-8")
            else:
                s = str(s)
            result += s
        return result

    def getUnboundVars(self):
        res = []
        for i in range(len(self.d)):
            if i % 2 == 1:
                res.append(self.d[i])
        return res


class Template:

    def __init__(self, template):
        self.keyDef = KeyDef.get(template)
        #print "TEMPLATE %s" % self.keyDef.getUnboundVars()

    def __call__(self, ctx):
        return self.keyDef.apply(lambda k: ctx[k])