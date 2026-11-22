# ThamesRowingSteering

Tools for visualising GPS traces from coxing and rowing the Head of the River Race
(HORR) course.

## Plot the fairway

Create the workspace virtual environment with 64-bit Python 3.15 in PowerShell,
then install the plotting dependency:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\plot_course.py
```

VS Code is configured to use `.venv` as the workspace interpreter and recommends
the Python and Pylance extensions. If VS Code was already open when `.venv` was
created, select `.venv\Scripts\python.exe` with **Python: Select Interpreter**.

Running `plot_course.py` shows both fairway limits, the calculated centreline,
buoys, and every GPX track found under `GPS_traces`. Use the figure's year, race,
boat-class, and steerer checkboxes to filter traces; matching selections within
a category are combined, and categories are combined together. The buoy-label
checkbox toggles buoy names. A table beside the plot lists each trace's tags,
mean and maximum centreline deviation, time and percentage outside the channel,
and recorded duration.

Track tags are read from the folder and filename: the first folder under
`GPS_traces` is the year, the race and boat class are inferred from
underscore-delimited filename tokens, and tokens after the boat class are used
as the steerer name. `HORR` and `WEHORR` are separate race tags. For example,
`GPS_traces\2024\Fours_Head_4x_Alex_Smith.gpx` is tagged as year 2024, race
Fours Head, boat class 4x, steerer Alex Smith. Missing or unrecognized tags are
shown as `Unknown`.

`course_data.py` reads KML/GPX, `course_drawing.py` contains reusable plotting
functions, and `course_analysis.py` contains the centreline, fairway geometry,
and steering metrics. These functions are intended to be reused as additional
race, boat, and steerer filters and visualisations are added.
