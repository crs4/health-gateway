.. Health Gateway documentation master file, created by
   sphinx-quickstart on Tue Oct  3 11:03:55 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Health Gateway Documentation
============================

Health Gateway Pilot: Project Aim
---------------------------------
This Project is a pilot study focused on the creation of **best-practices, from a
technical and a legal point of view, to enable automatic clinical data transfers from
public and private institutions to one or more repository selected by citizen**
(https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-016-0323-y).
The basic idea is that people are the owners of their data and must have the possibility of
managing them, deciding directly all the aspects connected to data storing and sharing.
In this model, a person can decide to automatically transfer the data to the desired destinations
(dropbox-like repositories, clinical trials, apps,...), selecting the kind of data to transfer
and the time constraints and giving a specific consent, which can be revoked in any time. This
implies the definition of a **model for a structured and dynamic consent**, allowing a person to directly
control targets, treatment and purposes for each single data, coming from different sources.
This paradigm implies a deep analysis about security, privacy and about ethical, legal and social
implications connected to data consent and management, from acquisition to destination.

This Project is a pilot, focused on exploring security aspects and legal implications.
From the technical point of view, it will be designed a generic architecture with a central core
(Health Gateway) devoted to ensure consent management and secure transfer from a generic source to a
generic destination. Mechanisms about secure authentication, consent confirmation and secure data
transfer will be analyzed. From the legal point of view, the whole process will be analyzed considering
the present legislation perspective (Italian and international), to develop a valid legal protocol to enable
data transfer according to the citizens will. The Project results include the development of a reference
implementation, compliant with the legal protocol developed and connected to Sardinian Region General
Practitioner Information system.

This Document
-------------

This document describes a generic architecture to support the structured and dynamic
consent model and the reference implementation of the platform, including the prototypal configurations.


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    architecture.rst
    modules/hgw_frontend/home.rst
    modules/consent_manager/home.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
=======

License
=======

Health Gateway is released under the MIT License (MIT)

::

    Copyright (c) 2017-2018 CRS4

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
    AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



