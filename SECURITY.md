# Security notes

## Save files and trust boundaries

The native roster file (`save.dat`) is currently Python-pickle based for backward compatibility. **Only load roster files you trust.** A pickle is not a safe untrusted interchange format: loading a crafted file can execute code with the permissions of the current user. Do not download a native save from an unknown source and place it in the pqcli configuration directory.

For exchanging characters, prefer the game's `.pqw` import/export format. It is base64-encoded JSON and is parsed as data rather than as a Python object graph. As with any input parser, keep pqcli updated and do not treat imported data as automatically trustworthy.

## Backups and recovery

Before manually modifying a save, stop pqcli and back up both `save.dat` and `save.dat.old` if present. The application preserves the previous roster on normal subsequent saves, but a backup is not a substitute for a separate copy.

## Reporting an issue

When reporting a crash, include the pqcli version, Python version, operating system, exact command, and a redacted traceback. Never attach a native pickle save unless you understand and accept its security implications.
