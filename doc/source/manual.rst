===============
End user manual
===============

This section describes the ``wxFrog`` client from an end-user's view. Most of the content relates to the simple *hello_world* example of the previous section.


Main frame appearance
=====================
.. image:: figures/hello_world_mainview.png

As shown above, the window shows the background image (here a simple square) over a specified background colour. The **blue labels** represent **model parameters**, while the **black labels** represent **model results**. Both types show a tooltip when the mouse is hovered over the label.

If the canvas is larger than the window, one can scroll by using the

- scrollbars
- cursor keys
- mouse-wheel, here holding shift for horizontal scrolling

File menu
---------
The file menu contains the common items to **open and save** the state of the simulation. This includes

- Parameter values
- Obtained results
- Potential internal states of the calculation engine
- Definition of the sensitivity study

The former three items are stored individually for each defined *scenario* (:ref:`see below <Scenario manager>`).

The **Export canvas** function stores the current canvas as a graphics as a png file, so it can easily be included in any documentation.

The **Copy stream table** function hints to the main purpose of this package, namely to be a frontend for models of chemical processes. In this case, the concept of streams is introduced to describe the transport of material and energy, such as power and heat. This function defines a well-formatted table and places it into the clipboard, **to be pasted in Excel**.

Finally, the **Exit** item is self-explanatory -- it makes the PC grow legs and exit the room.

Engine menu
-----------
**Run model** starts a model calculation, typically after changing the values of some parameters. The item is only enabled after the model is initialized, and while no other calculation is running.

**Case study** opens the case study dialog (:ref:`see below <Case studies>`).

View menu
---------
*Monitor* starts the engine monitor. This is where the output of the calculation engine is printed. This can be in particular useful if the engine fails to calculate or consumes a lot of computation time.

**Scenarios** starts the scenario manager (:ref:`see below <Scenario manager>`).

**All results** shows all results of the model. These can be considerably more than those displayed in the canvas (see below).

Help menu
---------
This menu only contains the **About** item, displaying some basic information of the application.


Particular dialog windows
=========================

.. _Parameter dialog:

Parameter dialog
----------------
.. image:: figures/parameter_edit.png

The parameter dialog appears when clicking on a parameter (blue label). One can edit the magnitude and select another unit of measurement. It is also possible to enter any compatible unit that is understood by `Pint`_.

While the link button is active, changing the unit will convert the magnitude into the new unit.
With a deactivated link button, the magnitude will not be updated when the unit is changed.

When a new valid unit is entered, this will be made available for the entire application.

Each parameter has a validity range, defined by a minimum and maximum value. Entering values outside this range is not permitted. In this case, an error message will be displayed below the input fields, indicating the valid range in the currently selected unit of measurement.

Once the new parameter value is committed, its label will appear in bold until the next calculation is performed.

.. _Scenario manager:

Scenario manager
----------------
.. image:: figures/scenario_manager.png

The scenario manager helps to maintain several scenarios and switch between them without the need of storing a multitude of files. There are three scenarios defined by default, each of them starting with an asterisk ``*``.
- ``* Default``: This scenario contains the default state for the model (factory settings if you will).
- ``* Active``: This is the current configuration, including parameters that just have been modified without recalculation.
- ``* Converged``: This is the last converged state of the model, containing a consistent set of parameters and results.

Any user-defined scenarios appear below. These cannot start with an asterisk.

The following actions can be performed on scenarios, triggered by the right-click (context) menu:

- ``Keep``: This action will save the selected scenario as a new user-defined one. It is available for the ``* Active`` and the ``* Converged`` scenario.
- ``Activate``: This action will apply the selected scenario as the active one. It is available for all but the ``* Active`` scenario.
- ``Rename``: Any custom scenario can be renamed this way.
- ``Delete``: Any custom scenario can be deleted this way.

.. _Case studies:

Case studies
------------
.. image:: figures/case_study_main.png

To run a case study, one or more parameters are selected using the ``+`` button. If multiple parameters have been included, the arrow buttons can be used to rearrange their sequence. Selected parameters can again be removed via the cross-button.

When a parameter is inserted, the default setting is to step in 5 steps from -10 % to +10 % of the current value. This can be altered by the following ways by double-clicking on the particular cells:

- The **minimum and maximum values** can be changed within the validity range of the parameter at hand. If the steps are specified (default), the increment value will change according to the new interval. Otherwise the number of steps will change.

- The **increment** can be specified. As such, it will yield a new value for the number of steps. If the interval divided by the increment is not an integer, an additional step is added to evaluate the model at the maximum value. For instance:

  === === ========= ============
  Min Max Increment Steps
  === === ========= ============
  1   10  2         1 3 5 7 9 10
  1   10  3         1 4 7 10
  === === ========= ============
