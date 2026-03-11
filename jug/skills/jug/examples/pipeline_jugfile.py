"""
Two-stage pipeline jugfile using bvalue().

Problem: we don't know how many stage-2 tasks to create until stage-1 runs.
Specifically, `split_data` returns a list of filenames whose count depends on
the input — we can't know it at import time.

Solution: use bvalue() to pause jugfile parsing until the split task is done,
then build stage-2 tasks from the actual list of filenames.

Task graph (first pass — before split_data runs):

    split_data(raw_file)     <- only task jug sees on first pass

Task graph (second pass — after split_data has finished):

    split_data(raw_file)
      -> process_chunk(chunk_0)  \
      -> process_chunk(chunk_1)   --> merge(results)
      -> ...

Run with:
    jug execute pipeline_jugfile.py   # will do multiple passes automatically
    jug status pipeline_jugfile.py --short
"""

import os
from jug import TaskGenerator, bvalue

RAW_FILE = 'data/large_dataset.txt'
CHUNK_DIR = 'data/chunks'
CHUNK_SIZE = 1000   # lines per chunk


# ---------------------------------------------------------------------------
# Stage 1: split a large file into chunks
# ---------------------------------------------------------------------------

@TaskGenerator
def split_data(input_path, chunk_dir, chunk_size):
    """
    Split input_path into files of chunk_size lines each.
    Returns a sorted list of chunk file paths.
    """
    os.makedirs(chunk_dir, exist_ok=True)
    chunk_paths = []
    chunk_idx = 0
    outfile = None

    with open(input_path) as f:
        for line_no, line in enumerate(f):
            if line_no % chunk_size == 0:
                if outfile is not None:
                    outfile.close()
                chunk_path = os.path.join(chunk_dir, f'chunk_{chunk_idx:04d}.txt')
                chunk_paths.append(chunk_path)
                outfile = open(chunk_path, 'w')
                chunk_idx += 1
            outfile.write(line)

    if outfile is not None:
        outfile.close()

    return sorted(chunk_paths)


# ---------------------------------------------------------------------------
# Stage 2: process each chunk independently
# ---------------------------------------------------------------------------

@TaskGenerator
def process_chunk(chunk_path):
    """Process one chunk and return a partial result."""
    total = 0
    with open(chunk_path) as f:
        for line in f:
            total += len(line.strip())
    return total


@TaskGenerator
def merge(partial_results):
    """Combine all partial results into a final answer."""
    return sum(partial_results)


# ---------------------------------------------------------------------------
# Build task graph
#
# First pass:
#   - split_data task is created and registered.
#   - bvalue(chunks_task) raises BarrierError because split_data hasn't run.
#   - jug stops parsing here and runs split_data.
#
# Second pass (after split_data completes):
#   - bvalue(chunks_task) succeeds and returns the actual list of paths.
#   - The for-loop creates one process_chunk task per chunk.
#   - merge is created with all process_chunk tasks as its dependency.
# ---------------------------------------------------------------------------

chunks_task = split_data(RAW_FILE, CHUNK_DIR, CHUNK_SIZE)

# bvalue() blocks until chunks_task is complete, then returns its value.
# On first import (before split_data runs) this raises BarrierError and jug
# re-imports the jugfile after running the split_data task.
chunk_paths = bvalue(chunks_task)

partial_results = [process_chunk(path) for path in chunk_paths]
final_result = merge(partial_results)
