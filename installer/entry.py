"""PyInstaller entry point. Build via tools/build_exe.bat - the bundled
batterybar package is resolved through --paths src."""
from batterybar.__main__ import main

raise SystemExit(main())
