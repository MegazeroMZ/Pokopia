Pokopia Explorer
=================

Small Tkinter app to explore the `Pokopia.csv` data.

Original csv data file came from https://github.com/JEschete/PokopiaPlanning

Features implemented:
- Treat `Specialty 1` and `Specialty 2` the same (combined into `specialties`).
- Treat `Favorite 1..6` the same (combined into `favorites`).
- Search by name (partial match).
- Filter by specialty or favorite.
- Sort by any column in the CSV or combined columns.
- View full details for a row.
- From a selected Pokémon, find related Pokémon that share habitats; group related results by favorite.

Run (Windows PowerShell):

```powershell
python app.py
```

Or run the smoke test:

```powershell
python smoke_test.py
```

Building the exe (Windows)
-------------------------

A convenience PowerShell script is included to build a single-file Windows executable using PyInstaller.

From PowerShell in the repository root:

```powershell
.\build_exe.ps1
```

What the script does:
- Installs/updates PyInstaller in the active Python environment.
- Runs PyInstaller with the project `app.py` as entrypoint and bundles `Pokopia.csv` into the exe (so the CSV is embedded).

Notes and alternatives:
- If you prefer the CSV to remain external (so it can be edited without rebuilding), edit `build_exe.ps1` and remove the `--add-data` option.
- Ensure you're using a compatible Python version (3.8–3.11 recommended) and that the Python architecture (32/64-bit) matches the target platform.
- The produced exe is placed in `dist\Pokopia\Pokopia.exe` by PyInstaller.
- Building requires network access for pip unless PyInstaller is already installed.

If you want, I can run the build here and return the produced exe (note: that will install packages in the environment and produce a binary). 
