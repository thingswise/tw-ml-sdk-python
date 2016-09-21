=====
Usage
=====

Device Metadata Query
=====================

To construct a data query in some cases device metadata may be needed. It
the configured `jets` project provides device metadata query, the code like
follows may be used:

.. code-block:: python

  devices = [ ... device ids ... ]

   meta_query = MetadataQuery(
     jets_url="your-jets-url",
     input_data=devices,
     progress=Progress("Device Query")
  )

Jets URL is used to query the specific endpoint in the project. Its format
is as follows::

  http[s]://{clientid}:{secret}@{host:port}/jets/streams/{scope}/{project}/{stream}

For every device ID listed in `input_data` parameter there will be a GET query
with `deviceId` parameter set to that element. The result will be interpreted
as a bag of key-value pairs. The values can be used later in the query
template substitution.

Device Data Query
=================

To query device timeseries data the code like follows can be used:

.. code-block:: python

  data_query = DataQuery(
        qapi_url="your-qapi-url",
        templates={
            "coord1": Template("query1..."),
            "coord2": Template("query2..."),
            ...
        },
        period="1min",
        interval=interval,
        _from=_from_,
        _to=_to_,
        key=lambda x: x["deviceId"],
        input_data=meta_query,
        input_data_len=1,
        progress=Progress("Data Query"),
        aggregation="sum"
    )

* `qapi_url` specifies the QAPI url to query and it has the following syntax::

    http[s]://{clientid}:{secret}@{host:port}/qapi/{scope}/{project}

* `templates` is a dictionary of named templates. Every template comes in
  the rule engine declarative syntax (e.g. :code:`A for {X}|{Y} by 1min`). The
  template parameters will be substituted using the `input_data` values
  (see below). They all must have the same period and it should be equal to
  the value provided in the `period` argument (see below). The interval
  between `_from` and `_to` will be diveded into non-overlapping subintervals
  of the length `interval`. For every input data element and every subinterval
  the result of the
  query will have a separate element called `Vector`. The vector consists
  of a collection of timeseries (`coordinates`) corresponding to the results
  of the queries, one for every defined template. To access a particular
  `coordinate` one can use the following code:

  .. code:: python

    vector.timeseries("coord1") # results in a list of DataPoints

* `period` defines the resolution of the query. Must be consistent with  the
  periods used in the templates

* `interval` (seconds) defines the length of subintervals into which the
  big interval (defined by `_from` and `_to`) is broken

* `_from` (seconds) -- the start of the query interval. If positive it indicates
  the number of seconds since Unix Epoch, if negative or zero it is added to
  the current unix epoch timestamp

* `_to` (seconds) -- the end of the query interval. If positive it indicates
  the number of seconds since Unix Epoch, if negative or zero it is added to
  the current unix epoch timestamp

* `key` -- a function to obtain a key for the given vector. Assuming
  :code:`key=f`, then for input data element :code:`x` the vector key
  will look like :code:`f(x):start` where :code:`start` is the start
  of the corresponding subinterval

* `input_data` (iterable or :class:`MetadataQuery`) -- the sequence of device
  objects for which the
  queries are to be run. Every element should be a dictionary which values
  will be used to substitute the parameters in the templates

* `input_data_len`   -- the length of the input data sequence

* `progress` -- the progress indicator callback

* `aggregation` -- the type of aggregation field to extract from the queried
  data. The supported values are:

  - `sum`
  - `avg` or `val`
  - `cnt`
  - `max`
  - `min`
  - `stddev`

Executing method :code:`get()`   of the :code:`DataQuery` object returns
an iterable of the obtained :code:`Vectors`. Each :code:`Vector` has a
unique key and a number of :code:`coordinates` (named timeseries). To
get a particular timeseries, use the call like follows:

.. code:: python

  vector.timeseries("coord1")

This returns a list of :code:`DataPoints`. Every one of them has two fields:

* `ts` -- timestamp (seconds since Unix Epoch)
* `value` -- the extracted value (float)

Utility Functions
=================

The obtained timeseries can be post-processed to filter certain values,
extract features, etc.

TimeseriesCollectionFeatureCoordinateExtractor
----------------------------------------------

Consider the following code:

.. code:: python

  vectors = list(data_query.get())
   extractor1 = { "scaled_sum": Scale(1.0/80, Sum()) }

   vectors_1 = VectorList(filter(lambda v: v["scaled_sum"] != 0, Extract(
        extractor=TimeseriesCollectionFeatureCoordinateExtractor(
            _from=_from_,
            _to=_to_,
            window=window,
            step=window,
            coordExtractor= {
                "coord1": extractor1
            }
        ))(vectors)))

The first line:

.. code:: python

  vectors = list(data_query.get())

stores the list of the obtained :code:`Vectors` in the variable :code:`vectors`.

Then it creates an :code:`Extract` instance and applies it to the list of
vectors, thus obtaining another list :code:`vectors_1` which contains not
timeseries, but vectors of features extracted from the original timeseries.

:code:`Extract` constructor takes one argument :code:`extractor` which it applies
to :code:`vectors`. In this case the extractor is :code:`TimeseriesCollectionFeatureCoordinateExtractor`,
the extractor that takes a collection of timeseries and converts it into a
collection of real values.

The arguments of its constructor are:

* `_from` -- the starting point in the input timeseries: seconds since Unix Epoch
* `_end` -- the end point in the input timeseries: seconds since Unix Epoch
* `window` and `step` -- within the `[_from,_end)` interval we take a number
  of subintervals of the length `window` at the step `step`
* `coordExtractor` -- for every such subinterval a corresponding subsequence
  is selected from each timeseries in the input data vector. Since timeseries
  are named, `coordExtractor` provides a mapping between timeseries names and
  extractor function. Every extractor function will get the particular
  timeseries subsequence and generate a bag of key-value pairs representing
  a subset of coordinates in the output vector. It is important that
  output coordinates are unique across extractor definitions. Consider the
  following `coordExtractor` definition:

  .. code:: python

    coordExtractor = {
       "in_coord1": {
         "out_coord1": extractor1,
         "out_coord2": extractor2
       },
       "in_coord2": {
         "out_coord3": extractor3
       }
     }

  This spec instructs the extractor algorithm to create the vector
  `(out_coord1, out_coord2, out_coord3)` from timeseries
  `in_coord1` and `in_coord2`. In particular, `out_coord1` and `out_coord2`
  will be obtained from a subinterval of `in_coord1` using `extractor1` and
  `extractor2`, while `out_coord3` will be obtained from a subinterval of
  `in_coord2` using `extractor3`
