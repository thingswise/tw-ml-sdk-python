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

from ._version import get_versions
__version__ = get_versions()['version']
#del get_versions

from metadata_query import MetadataQuery
from template import Template
from data_query import DataQuery
from model_helper import Filter, AndFilter,\
                         HasCoord, TimeseriesFeatureExtractor, TimeseriesFeatureCoordinateExtractor,\
                         OnTimeExtractor, StopsExtractor, Extract, Progress, ModelHelper, Scale, \
                         Sum, TimeseriesCollectionFeatureExtractor, TimeseriesCollectionFeatureCoordinateExtractor, \
                         diag_vect, matrix, stack, VectorList
from models import Model, Scatter, KMeansModel, KMeansModelFactory                          
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
