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

class Model:
    
    def gen(self):
        """Generate and return a dictinary representing a serializable model
        definition compatible with TW runtime environment
        """
        pass

    def scatter2d(self):
        """Create a Scatter object that represents a 2-D visualization of the
        model
        """
        pass        

class Scatter:
    """Information container for plotting a 2-D scatter plot.

    Attributes:
        x           Array of X coordinates
        y           Array of Y coordinates
        c           Array of class labels        
    """
    def __init__(self, x, y, c):
        self.x = x
        self.y = y
        self.c = c

class KMeansModel(Model):
    """Representation of a K-Means model.
    
    Attributes:
        km          sklearn.cluster.KMeans object        
    """
    def __init__(self, km, coords, init_labels, points):
        """Construct a KMeansModel object.

        Arguments:
            km      The sklearn.cluster.KMeans object that holds the model
            coords  A list of coordinate labels. Since every row in the
                    datapoint matrix corresponds to a real vector, the ordered
                    list of coordinate labels provides the textual names (labels)
                    for the items in that vector. When exporting the model
                    the labels will appear in the cluster coordinate object
            init_labels
                    The list of input (observed) labels for the datapoints. The
                    size of the list must be equal to the size of the training set
            points  The coordinates of the training set in the form of a matrix
                    where every row is an element of the training set 
        """
        self.km = km
        self.coords = coords
        self.init_labels = init_labels
        self.points = points
    
    def gen(self):
        possible_labels = {}
        for i in xrange(self.init_labels.shape[0]):
            possible_labels[int(self.init_labels[i])] = True
        cluster_labels = []
        for i in xrange(self.km.cluster_centers_.shape[0]):
            cluster_labels.append({"by_label": {k:0 for k in possible_labels} })
        for i, l in enumerate(self.km.labels_):
            cl = cluster_labels[l]
            il = self.init_labels[i]
            cl["by_label"][int(il)] += 1
        for i, l in enumerate(cluster_labels):
            total = 0
            _max = 0
            _argmax = -1
            for k, v in l["by_label"].iteritems():
                total += v
                if _max <= v:
                    _argmax = k
                    _max = v
            if _argmax == -1:
                raise ValueError("Cannot determine label for cluster %d" % i)
            l["total"] = total
            l["label"] = _argmax
        
        return {
            "type": "kmeans/euclidean",
            "clusters": [
                {
                    "coordinates": {
                        c : self.km.cluster_centers_[ci][i] for i, c in enumerate(self.coords)
                    },
                    "label": cl["label"],
                    "by_label": cl["by_label"]
                } for ci, cl in enumerate(cluster_labels)
            ]
        }
    
    def scatter2d(self):
        if self.points.shape[1] == 2:
            return Scatter(x=self.points[:,0].T.A.ravel(),y=self.points[:,1].T.A.ravel(),c=self.init_labels)
        else:
            raise ValueError("Incompatible point matrix dimension: %d (must be 2)" % self.points.shape[1])
    
    
class KMeansModelFactory:
    
    def __init__(self, coords):
        self.coords = coords
        
    def run(self, M, n_clusters):
        import sklearn.cluster as cls

        km = cls.KMeans(n_clusters=n_clusters)

        labels = km.fit_predict(M[:,0:-1])
    
        return KMeansModel(km, self.coords, M[:,-1].T.A.ravel(), M[:,0:-1])
