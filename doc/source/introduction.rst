============
Introduction
============

The first part of the name ``WxFrog`` obviously comes from ``wxWindows`` or ``wxPython``, simply because the graphical interface is implemented based on it. The second part is obviously an animal, which is always fun, but stretching it (not the animal, please), it can stand for **fro**-ntend **g**-eneric -- I know!

Please let us not think too much more about the name.

Hello World
===========

Python code
-----------
A nearly smallest possible application is described here. It shows a schematic rectangle with the measures of the two distinct edges and calculates the surface area and perimeter of it. All required code for the GUI application is the following:

.. exampleinclude:: hello_world/gui.py
    :language: python
    :linenos:

**Line 1:** In case the application is to be packaged, the most robust way to deal with input data is to utilise the :mod:`importlib.resources` library. The :func:`~importlib.resources.files` function returns a :class:`~importlib.resources.abc.Traversable` object representing the directory of the specified module.

**Line 2:** ``start_gui()`` is the entry function that creates the GUI application and enters the event loop. ``CalculationEngine`` is the abstract baseclass to be implemented for the specific model at hand. ``get_unit_registry()`` fetches the currently installed :class:`~pint.UnitRegistry` object, which is per default a nearly vanilla :class:`pint.UnitRegistry` instance.

**Line 4:** As :class:`pint.Quantity` objects, are to be created, we obtain the correct reference here. As by design of `Pint`_, all instances need to origin from the same registry. ``wxfrog`` keeps that singleton available via ``get_unit_registry``.

**Lines 7-13:** The class defines our model with two required methods. ``get_default_parameters()`` is to return a (nested - if desired) dictionary of default parameters, represented as :class:`pint.Quantity` objects. The returned structure also fixes the set of parameters of which the application will be aware of. In other words: Here is an opportunity to filter out internal or advanced parameters that are not to be shown in the application. The ``calculate()`` method can expect a parameter dictionary as previously returned by ``get_default_parameters``, with altered quantities but compatible with the original ones in terms of physical dimensions. It is simply to return another (nested - if desired) dictionary of the results.

.. note::

    All values are scalars. Please don't start the show passing arrays as magnitudes here.
    Admittingly, this could be fun - and the graphical application could show graphs of it.
    Dream on -- this is not happening soon!

**Line 16:** The call to the entry point is enclosed in the ``main()`` function to make it easier to configure the application as an application. As such, we can for instance use ``pyproject.toml`` to define ``wxfrog_hello_world`` as a gui-script available on activation of the python environment:

.. code-block::

    [project.gui-scripts]
    wxfrog_hello_world = "wxfrog.examples.hello_world.gui:main"

**Line 17-20:** This function call starts, as mentioned above, the GUI event loop, which then expects all configuration and the background picture to be in the given directory. Line 19 instantiates and injects our rectangle model.

Application configuration
-------------------------
The missing part is the configuration of the application itself, given as follows:

.. exampleinclude:: hello_world/data/configuration.yml
    :language: yaml
    :linenos:

``app_name``: The name of the app -- used as the title in the main frame.

``file_ending``: File ending for files that can be saved, containing parameter sets, case studies, and internal states of the calculation engine (our rectangle model does not have that).

``about``: A simple definition of a custom about dialog, via html. However, this is as for now realised using the :class:`wx.html.HtmlWindow` with very limited rendering capabilities.

``about_size``: The size of the about dialog as ``[width, height]``.

``bg_picture_name``: The name of the background picture. In Linux, svg-graphics are supported as well, but in Windows, due to currently inconsistent code in the :mod:`wx.svg` module, only png-files can be processed.

``bg_picture_width``: The background picture will be scaled to the given width, keeping its aspect ratio. This is vital for svg, but still very useful even for png. Note that whenever this value is changed, the pixel positions specified for parameters and results below become invalid.

``font_size``: Depending on the eye-sight of your audience, this entry defines the font size for all labels and tooltips.

``bg_color``: As the background picture may have a transparent background, this color defines the background color. As this is implemented using :class:`wx.Colour`, the value here can be a colour name, such as ``white`` or ``green yellow``, or any color in the hexadecimal format ``#RRGGBB``.

``run_engine_on_start``: A boolean flag to indicate whether the calculation shall be performed already with the default parameters on start. One might chose to disable this option in case the model is heavy to calculate and thus blocks the user from starting the relevant calculation.

``parameters``: An array of the parameters to be displayed on the canvas. This can be a subset of the parameters exposed from the calculation engine. Each parameter has the following attributes:

- ``path``: The path in the nested dictionary to address this parameter. For non-nested parameter structures, this is a single entry.
- ``pos``: This is the position on the canvas as ``[horizontal, vertical]`` offset in pixels from the top left corner.

.. note::

    Pressing ``Ctrl`` while left-clicking on the canvas will dump a template entry with mouse coordinates to standard out and into the clipboard. This makes it eas(y|ier) to position the labels.

- ``uom``: A valid unit of measurement used for displaying the quantity. This must be compatible to the unit of the quantity given by the calculation engine.
- ``fmt``: A valid python format string for the quantity. We recommend to use the ``~P`` notation to print units of measurements compact and pretty.
- ``min`` and ``max`` A minimum and maximum value to prevent the user from entering infeasible input.

``results``: The results are defined in the same manner as parameters, only without definition of ``min`` and ``max``.

``units``: By default, all previously mentioned compatible units are available when changing a quantity in the GUI. With this entry, more entities can be added.

.. note:: Additionally, one can write any compatible unit into the combo-box of a quantity dialog. This will be accepted and then also added to the available units for that physical dimension.





