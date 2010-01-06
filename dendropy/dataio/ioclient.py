#! /usr/bin/env python

###############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2009 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

"""
Provides high-level brokerage between formats and associated parsers/writers.
"""

from dendropy.dataio.dataschema import DataSchemaRegistry

_GLOBAL_DATA_SCHEMA_REGISTRY = DataSchemaRegistry()

def register(schema, reader, writer, tree_source_iter):
    _GLOBAL_DATA_SCHEMA_REGISTRY.add(schema, reader, writer, tree_source_iter)

def get_reader(schema, **kwargs):
    """
    Returns a reader object of the appropriate schema-handler as specified by
    `schema`.

    `schema` is a string that is name of one of the registered data
    formats, such as `nexus`, `newick`, etc, for which a specialized
    reader is available. If this is not implemented for the schema
    specified, then a `UnsupportedFormatError` is raised.

    The following keyword arguments are recognized:

        - `dataset`: All data read from the source will be instantiated
                as objects within this `DataSet` object.
        - `taxon_set`: A`TaxonSet` object. If given, results in all the
                taxa being accessioned into a single `TaxonSet` (and all
                TaxonSetLinked objects instantiated being associated with that
                `TaxonSet` object), even if multiple taxon collection
                definitions are encountered in the source.
        - `exclude_trees`: Trees in the source will be skipped.
        - `exclude_chars`: Characters in the source will be skipped.
        - `encode_splits`: Specifies whether or not splits will be
                automatically-encoded upon a tree being read.

    Other keywords may be implemented by specific readers (e.g. NexusReader,
    NewickReader). Refer to their documentation for details.
    """
    return _GLOBAL_DATA_SCHEMA_REGISTRY.get_reader(schema, **kwargs)

def get_writer(schema, **kwargs):
    """
    Returns a writer object of the appropriate schema as specified by `schema`.

    `schema` is a string that is name of one of the registered data
    formats, such as `nexus`, `newick`, etc, for which a specialized
    writer is available. If this is not implemented for the schema
    specified, then a `UnsupportedFormatError` is raised.

    The following keyword arguments are recognized:

        - `dataset`: A `DataSet` object that will be the default source of the
                data to be written.
        - `exclude_trees`: Trees in the `DataSet` or `TaxonDomain` will not be
                written.
        - `exclude_chars`: Characters in the `DataSet` or `TaxonDomain` will
                not written.
    """
    return _GLOBAL_DATA_SCHEMA_REGISTRY.get_writer(schema, **kwargs)

def tree_source_iter(stream, schema, **kwargs):
    """
    Returns an iterator over trees in `schema`-formatted data
    in from file-like object source `stream`. Keyword arguments
    are passed to schema-specialized implementation of the iterator
    invoked.

    Keyword arguments accepted (handled here):

        - `tree_offset` 0-based index specifying first tree to actually return
           (raises KeyError if >= #trees)

    Keyword arguments that should be handled by implementing Readers:

        - `taxon_set` specifies the `TaxonSet` object to be attached to the
           trees parsed and manage their taxa. If not specified, then a
           (single) new `TaxonSet` object will be created and for all the
           `Tree` objects.
        - `encode_splits` specifies whether or not split bitmasks will be
           calculated and attached to the edges.
        - `finish_node_func` is a function that will be applied to each node
           after it has been constructed.
        - `edge_len_type` specifies the type of the edge lengths (int or float)

    """
    if "tree_offset" in kwargs:
        tree_offset = kwargs["tree_offset"]
        del(kwargs["tree_offset"])
    else:
        tree_offset = 0
    if "write_progress" in kwargs:
        write_progress = kwargs["write_progress"]
        del(kwargs["write_progress"])
    else:
        write_progress = None
    tree_iter = _GLOBAL_DATA_SCHEMA_REGISTRY.tree_source_iter(stream, schema, **kwargs)
    for count, t in enumerate(tree_iter):
        if count >= tree_offset and t is not None:
            if write_progress is not None:
                write_progress("Processing tree at index %d" % count)
            count += 1
            yield t
        else:
            if write_progress is not None:
                write_progress("Skipping tree at index %d" % count)
    if count < tree_offset:
        raise KeyError("0-based index out of attacheds: %d (trees=%d, tree_offset=[0, %d])" % (tree_offset, count, count-1))

def multi_tree_source_iter(sources, schema, **kwargs):
    """
    Iterates over trees from multiple sources, which may be given as file-like
    objects or filepaths (strings). Note that unless a TaxonSet object is
    explicitly passed using the 'taxon_set' keyword argument, the trees in each
    file will be associated with their own distinct, independent taxon set.
    """
#    if "taxon_set" not in kwargs:
#        kwargs["taxon_set"] = TaxonSet()
    if "write_progress" in kwargs:
        write_progress = kwargs["write_progress"]
        del(kwargs["write_progress"])
    else:
        write_progress = None
    num_sources = len(sources)
    for i, s in enumerate(sources):
        if isinstance(s, str):
            src = open(s, "rU")
        else:
            src = s
        if write_progress is not None:
            write_subprogress = lambda x: write_progress("Tree source %d of %d: %s\n"
                    % (i+1, num_sources, str(x)))
        else:
            write_subprogress = None
        for t in tree_source_iter(src, schema, write_progress=write_subprogress, **kwargs):
            yield t