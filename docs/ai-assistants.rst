=========================
AI Assistant Integration
=========================

Jug ships with a bundled ``jug`` skill for coding assistants that support
skills directories.

Installing the skill
--------------------

Install the bundled skill into a user-level skills directory with::

    jug install-skills --output ~/.codex/skills

This copies the bundled files to ``~/.codex/skills/jug``. Use ``--force`` to
replace an existing copy.

For a project-local Claude Code install, use::

    jug install-skills --output .claude/skills

This copies the same files to ``.claude/skills/jug`` inside your repository.

Using the skill with Codex
--------------------------

Codex looks for skills in ``$CODEX_HOME/skills`` (typically
``~/.codex/skills``). After installing the bundled skill there, invoke it
explicitly in your prompt, for example::

    Use $jug to write a jugfile for this pipeline.

or::

    Use $jug to debug why these tasks are stuck waiting.

Using the skill with Claude Code
--------------------------------

Claude Code discovers skills from ``~/.claude/skills`` and project-local
``.claude/skills`` directories. After installing the bundled skill there, start
Claude Code in your project and invoke the skill as ``/jug`` or select it from
the skills menu.

Typical prompts are::

    /jug explain this jugfile

or::

    /jug help me refactor this workflow to use barriers safely

What gets installed
-------------------

The bundled skill includes:

* ``SKILL.md`` with the main Jug workflow guidance
* ``references/`` for CLI reference, common patterns, and troubleshooting
* ``examples/`` with minimal jugfile examples
* ``agents/openai.yaml`` for Codex/OpenAI UI metadata
