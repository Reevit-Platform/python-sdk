# Single source of truth for the SDK version.
# Read by setup.py (via exec, without importing the package) and by
# client.py for the X-Reevit-Client-Version header. Keep this file
# free of imports so it stays loadable in build environments where
# runtime dependencies are not installed.
__version__ = "0.10.0"
