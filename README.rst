====
Dame
====

Dame is a `SIR <http://www.mers.byu.edu/SIR.html>`_ file viewer. It's focused on comparing and interpreting two SIR files together. It is written in Python using the Qt toolkit, so it should be cross-platform, but has only been tested on Linux.

Dame is distributed under the MIT license.

Dependencies
============

* Python 2
* PyQt4
* NumPy
* libsir

Features
========

Dame can:

* Load a SIR image (using the C SIR library)
* Pan around the image by right-click dragging
* Display information about the currently selected pixel
* Display the pretty-printed SIR header
* Popup a magnified view of the selected region

Installation
============

Arch Linux
----------

`dame is in the AUR <https://aur.archlinux.org/packages/dame-git/>`_, along with `libsir <https://aur.archlinux.org/packages/libsir/>`_, an important dependency.

Elsewhere
---------

Ensure the standard dependencies are installed (Python, PyQt4, etc). The SIR C library requires a little more effort. 

Download `libsir from the MERS lab <ftp://ftp.scp.byu.edu/software/misc/sirclib.tar.gz>`_. It needs a few modifications to compile with a modern version of glibc. Also, the Makefile requires modifications to compile a shared library. Patches are available on the `libsir AUR page <https://aur.archlinux.org/packages/libsir/>`_, I recommend taking a look at the PKGBUILD and the patches to see how to compile and install libsir.

With libsir installed, dame should run just fine.

Changelog
=========

v0.2 2013-xx-xx

* Some bugfixes
* Add keyboard shortcuts for nagivation (not implemented yet)

v0.1 2013-09-12

* Implemented basic functionality (load SIR, pan, show zoomed region)

