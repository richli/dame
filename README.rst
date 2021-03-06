====
Dame
====

Dame is a `SIR <http://www.mers.byu.edu/SIR.html>`_ file viewer. It's focused on comparing and interpreting two SIR files together. It is written in Python using the Qt toolkit, so it should be cross-platform, but has only been tested on Linux.

Dame is distributed under the MIT license.

Dependencies
============

* Python 2.7 or Python 3.3
* PyQt4 or PySide
* NumPy
* libsir

Features
========

Dame can:

* Load a SIR image (using the C SIR library)
* Display the pretty-printed SIR header
* Pan around the image by middle-click dragging
* Display information about the currently selected pixel
* Popup a magnified view of the selected region
* Use keyboard shortcuts to move crosshair (hjkl to move one pixel, use shift to move five pixels)
* Change image display range
* Store temporary notes in a dock widget
* Comparison view

  * Split view of two SIR files
  * For a given pixel, display the SIR values for both images simultaneously
  * Crossfade between the two SIR files (coming soon)
  
Screenshot
==========
.. image:: http://i.imgur.com/6sRidwW.png

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

v0.6 IN PROGRESS

* The zoomer window shows both sides during split view
* Code now runs on Python 2 and 3 (tested with 2.7 and 3.3)
* Code now runs with PyQt4 or PySide
* Minor bugfixes

v0.5 2013-11-20

* Bugfix: images with a width not a power of 4 were warped really weird

v0.4 2013-09-27

* Add comparison mode with split view
* Change mouse panning from right-click to middle-click
* Add a "notes" dock widget
* More bugfixes

v0.3 2013-09-25

* Add dialog to change image display range
* Improved image loading speed
* Several bugfixes

v0.2 2013-09-13

* Add keyboard shortcuts for nagivation (vim-like)
* Some bugfixes

v0.1 2013-09-12

* Implemented basic functionality (load SIR, pan, show zoomed region)

