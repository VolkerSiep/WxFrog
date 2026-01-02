# WxFrog

`WxFrog` is a generic user interface for a steady-state calculation engine, based on the following idea:

  - Present a picture as a static background for the canvas, typically a drawing of the system / process that is to be represented.
  - Position text labels at static locations, whereas the labels represent mutable model parameters and calculated properties.
  - Both properties and parameters are communicated via nested dictionaries with strings as keys and `Pint` quantities as values - allowing full flexibility in terms of units of measurements and number formatting.
  - Run calculations and case studies.
  - Allow to load and save files, including parameter sets, internal states of the calculation engine, and case study scenarios.
  - Export case study results and structured tables of data as tables to spreadsheet software.
  - No UI programming required for application code. All configuration is defined in a `YAML` file.