# Configuration

## Configuration file

```{versionadded} 1.3
In previous versions, the configuration file was called `~/.jug/configrc`. Since version 1.3, the path `~/.config/jugrc` is used (for compatibility, `~/.jug/configrc` is read if `~/.config/jugrc` is missing).
```

On startup, `jug` reads the first of the files `~/.config/jug/jugrc`,
`~/.config/jugrc`, and `~/.jug/configrc` that exists (if any). It
expects an *.ini* format file. It can have the following fields:

```
[main]
jugdir=%(jugfile)s.jugdata
jugfile=jugfile.py

[status]
cache=off

[execute]
keep-going=off
wait-cycle-time=12
nr-wait-cycles=150
```

These have the same meaning as the analogous command line options. If both are
given, the command line takes priority. Settings in the `[main]` section
correspond to the global options (e.g., `--jugdir`), while settings in other
sections correspond to options of that subcommand (e.g., `wait-cycle-time` in
the `[execute]` section corresponds to `jug execute --wait-cycle-time`).
Boolean settings accept `on`/`off`, `true`/`false`, or `1`/`0`.

Note that the global flags `--aggressive-unload`, `--debug`, `--pdb`, and
`--short` cannot currently be set in the configuration file.

## Project-local configuration

In addition to the global configuration file, `jug` also searches for
project-local configuration files named `.jugrc` or `jugrc`. Starting from
the current working directory, `jug` walks up the directory tree looking for
these files. If the current directory is inside a git repository (i.e., a
`.git` directory is found), the search continues up to and including the
repository root. If no git repository is detected, only the current directory is
searched.

All found configuration files are applied with the following priority (highest
first):

1. Command-line arguments
2. Local config closest to the current directory
3. Local configs in parent directories (up to the project root)
4. Global configuration file (`~/.config/jug/jugrc`, etc.)
5. Built-in defaults

This allows you to place a `.jugrc` at the root of your project with
project-wide settings, and optionally override specific settings in
subdirectories.
