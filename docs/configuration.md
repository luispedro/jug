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

## Valid settings

The name of a setting is the name of the option it corresponds to (the
`dest` of the command line option, with `-` and `_` being interchangeable),
which is *not always* the same as the name of the command line flag (e.g.,
`jug graph --file-format` is `format` in the `[graph]` section). Unknown
settings are silently ignored. The settings that have an effect are:

| Section | Setting | Command line equivalent | Default |
|---------|---------|-------------------------|---------|
| `[main]` | `jugdir` | `--jugdir` | `%(jugfile)s.jugdata` |
| `[main]` | `jugfile` | `jugfile` argument | `jugfile.py` |
| `[main]` | `verbose` | `--verbose` | `quiet` |
| `[main]` | `short` | `--short` | `off` |
| `[main]` | `debug` | `--debug` | `off` |
| `[main]` | `pdb` | `--pdb` | `off` |
| `[main]` | `aggressive-unload` | `--aggressive-unload` | `off` |
| `[main]` | `will-cite` | `--will-cite` | `off` |
| `[execute]` | `wait-cycle-time` | `jug execute --wait-cycle-time` | `12` |
| `[execute]` | `nr-wait-cycles` | `jug execute --nr-wait-cycles` | `150` |
| `[execute]` | `keep-going` | `jug execute --keep-going` | `off` |
| `[execute]` | `keep-failed` | `jug execute --keep-failed` | `off` |
| `[execute]` | `no-check-environment` | `jug execute --no-check-environment` | `off` |
| `[execute]` | `name` | `jug execute --name` | (none) |
| `[execute]` | `pattern` | `jug execute --pattern` | (none) |
| `[status]` | `cache` | `jug status --cache` | `off` |
| `[status]` | `cache-file` | `jug status --cache-file` | `.jugstatus.sqlite3` |
| `[cleanup]` | `locks-only` | `jug cleanup --locks-only` | `off` |
| `[cleanup]` | `failed-only` | `jug cleanup --failed-only` | `off` |
| `[cleanup]` | `keep-locks` | `jug cleanup --keep-locks` | `off` |
| `[graph]` | `no-status` | `jug graph --no-status` | `off` |
| `[graph]` | `format` | `jug graph --file-format` | `png` |
| `[webstatus]` | `port` | `jug webstatus --port` | `8080` |
| `[webstatus]` | `ip` | `jug webstatus --ip` | `localhost` |

For example, to stop jug from printing the request for citation every time
`jug execute` finishes (once you have resolved to cite it, of course), add
the following to your configuration file:

```
[main]
will-cite=on
```

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
