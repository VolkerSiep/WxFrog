=======================
Configuration reference
=======================

The configuration file is to be provided in ``yaml`` format. The top=level dictionary contains the following entries, listed alphabetically:

about
=====
This is some html formatted content to briefly describe the program. No advanced styling is understood. A working example is the following:

.. code-block:: html

   <h3>WX-Frog example application V1.0b1</h3>
   <p><dl>
     <dt>License:</dt><dd>MIT AND (Apache-2.0 OR BSD-2-Clause)</dd>
     <dt>Author:</dt><dd>Volker Siepmann</dd>
     <dt>Year:</dt><dd>2025</dd>
   </dl></p>

:Type: string

about_size
==========
A pair of integers describing the width and height of the about window in pixels.

:Type: [int, int]

app_name
========
This is the name of the application, appearing for instance in the main frame window title.

:Type: string

bg_color
========
If the background picture has transparency, this color describes the background visible behind. The string must be a valid color from the `wx.ColourDatabase <https://docs.wxpython.org/wx.ColourDatabase.html#wx-colourdatabase>`_ or a hexadecimal RGB string, as for instance ``#FFFF00`` for bright yellow.

:Type: string


bg_picture_height
=================
This attribute and ``bg_picture_width`` determine the size of the background picture. If none of the attributes is specified, the original picture size is assumed. If one of the attributes is given, the missing attribute will be calculated by scaling under constant aspect ratio. If both attributes are given, the picture will be stretched into the specified dimensions.

.. note::

    Having control over the size of the background picture is essential to efficiently maintain the pixel positions of parameter and result labels (see ``parameters`` and ``results``).

:Type: int

bg_picture_name
===============
This is the name of the picture file, which must be located in the configuration directory.
Currently, only ``png`` files are supported on Windows, while additionally ``svg`` is supported on Linux.

:Type: string

bg_picture_width
================
See ``bg_picture_height``

:Type: int

file_ending
===========
A suffix, typically consisting of three characters, which is used to filter file names when offering to open or save simulation files.

:Type: string

font_size
=========
The size of the font used for labels and tooltips in the canvas.

:Type: int

parameters
==========
This is a list of parameter specifications, of which each is a dictionary with
the following entries:

path
----
The path of the parameter in the model as a ``list[str]``, such as ``[process, HX320, area]``.

pos
---
The position of the label to appear on the canvas as a list of two integers, defining horizontal and vertical position from the top left corner of the canvas.

.. note::

    Holding the ``ctrl`` key while left-clicking on the canvas will copy a template entry with the given mouse position into the clipboard -- to be augmented with the other attribute values. This enables efficient placements of the labels.

uom
---
The `Pint`_ compliant default unit of measurement used for the parameter as a string, as for instance ``degC`` or ``W/(m^2*K)``.

fmt
---

A python string with one placeholder for a `Pint`_ quantity, which is used to display the label on the canvas. A typical example is ``"Q = {:.2f~P}"``. This renders the value as a fixed digit number with two digits right of the decimal point. The unit of measurement is rendered compact (``~``) and formatted pretty (``P``). The latter means that sub- and superscripts, as well as greek letters are used to format the unit nicely.

min
---
The minimum allowable value for the parameter. The user will be prohibited to enter lower values either directly or as bounds in a case study.

max
---

The maximum allowable value for the parameter. The user will be prohibited to enter higher values either directly or as bounds in a case study.

:Type: list[dictionary]

results
=======
This is a list of result specifications, of which each is a dictionary similar to that of ``parameters``, except that ``min`` and ``max`` are not to be defined, as the calculated properties are what they are as given by the underlying model.

:Type: list[dictionary]

run_engine_on_change
====================

:Type: bool

run_engine_on_start
===================

:Type: bool

units
=====
In combo-boxes for units of measurements, compatible units used elsewhere are available as choices, and so are valid and compatible units that have typed into these combo-boxes.
This ``units`` list can provide additional units that shall be available by default for selection.

:Type: list[string]
