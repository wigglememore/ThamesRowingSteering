# ThamesRowingSteering

Tools for visualising GPS traces from coxing and rowing the Head of the River Race
(HORR) course.

## Plot the fairway

Create and activate the workspace virtual environment in PowerShell, then install
the plotting dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\plot_course.py
```

VS Code is configured to use `.venv` as the workspace interpreter and recommends
the Python and Pylance extensions. If VS Code was already open when `.venv` was
created, select `.venv\Scripts\python.exe` with **Python: Select Interpreter**.

By default the figure shows both fairway limits, the calculated centreline, and
the named navigation buoys. Overlay one or more GPS traces with `--track`, and
save the result instead of opening a window with `--save`. Add `--label-buoys`
to display buoy names:

```powershell
python plot_course.py --track "GPS_traces\2022\HORR_8+_Matt.gpx" --save course.png
```

Print mean and maximum centreline deviation plus the recorded time and
percentage outside the fairway with `--analyze`:

```powershell
python plot_course.py --track "GPS_traces\2022\HORR_8+_Matt.gpx" --analyze
```

`course_data.py` reads KML/GPX, `course_drawing.py` contains reusable plotting
functions, and `course_analysis.py` contains the centreline, fairway geometry,
and steering metrics. These functions are intended to be reused as additional
race, boat, and steerer filters and visualisations are added.
