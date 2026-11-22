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
named navigation buoys, and every GPX track found under `GPS_traces`.

`course_data.py` reads KML/GPX, `course_drawing.py` contains reusable plotting
functions, and `course_analysis.py` contains the centreline, fairway geometry,
and steering metrics. These functions are intended to be reused as additional
race, boat, and steerer filters and visualisations are added.
