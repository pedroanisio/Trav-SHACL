########################
Features and Limitations
########################

The current implementation of Trav-SHACL does not cover all features of the complete SHACL language.
The following is a list of what is supported:

*   simple cardinality constraints, i.e., ``sh:minCount`` and ``sh:maxCount``
*   datatype constraints, i.e., ``sh:datatype``
*   value-type constraints, i.e., ``sh:class`` and ``sh:nodeKind``
*   value-range constraints, i.e., ``sh:minInclusive``, ``sh:minExclusive``, ``sh:maxInclusive``, and ``sh:maxExclusive``
*   string constraints, i.e., ``sh:minLength``, ``sh:maxLength``, ``sh:pattern`` with ``sh:flags``, ``sh:languageIn``, and ``sh:uniqueLang``
*   property-pair constraints, i.e., ``sh:equals``, ``sh:disjoint``, ``sh:lessThan``, and ``sh:lessThanOrEquals``
*   relaxed shape-based constraints, i.e., ``sh:qualifiedValueShape`` with ``sh:qualifiedMinCount`` and ``sh:qualifiedMaxCount``
*   simple SPARQL constraints, i.e., ``sh:sparql`` with ``sh:select``

        +   ``sh:prefixes`` is currently not implemented, i.e., the query needs to use full URIs or specify the prefixes within ``sh:select``
        +   ``sh:message`` is ignored, i.e., the message is not included in the result
        +   only ``$this`` is supported as placeholder
*   simple logical constraints, i.e., ``sh:or``
*   inverse paths, i.e., ``sh:path [ sh:inversePath ex:your_predicate ]``
*   Trav-SHACL is capable of validating

        +   public SPARQL endpoints
        +   private SPARQL endpoints via HTTP Basic Auth (since v1.6.0)
        +   RDFLib graphs (since v1.3.0)

The following is a list of some of the more important features that are not yet covered:

*   ``sh:node``
*   ``sh:hasValue``
*   ``sh:and``
*   ``sh:not``
*   and others
