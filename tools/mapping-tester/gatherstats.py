#! /usr/bin/env python3

import argparse
import csv
import glob
import json
import os
import subprocess


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Gathers stats after a run")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("w"),
        default="stats.csv",
        help="The resulting CSV file containing all stats.",
    )
    return parser.parse_args(args)


def find_exact_event_name(file_path, pattern):
    # Create the grep command as a string
    command = f"grep -Po '.{{0,50}}{pattern}.{{0,50}}' {file_path}"

    # Run the command using subprocess
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        # Extract the matched line
        matched_line = result.stdout.strip()
        # Apply further regex to refine the result to exactly what we need
        exact_match = subprocess.run(
            ["grep", "-oP", pattern],
            input=matched_line,
            text=True,
            capture_output=True,
            check=True,
        )
        return exact_match.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        return None


def statsFromTimings(dir):
    stats = {}
    assert os.path.isdir(dir)
    assert (
        os.system("command -v precice-profiling > /dev/null") == 0
    ), 'Could not find the profiling tool "precice-profiling", which is part of the preCICE installation.'
    event_dir = os.path.join(dir, "precice-profiling")
    json_file = os.path.join(dir, "profiling.json")
    os.system("precice-profiling merge --output {} {}".format(json_file, event_dir))
    # first, generate the correct timings file for the computeMapping event (we want the most expensive rank for computeMapping)
    compute_mapping_timings = os.path.join(dir, "timings-computeMapping.csv")
    matching_event = find_exact_event_name(
        json_file, r'initialize\/map\.[^"]*computeMapping\.FromA-MeshToB-Mesh'
    )
    os.system(
        "precice-profiling analyze --event {} --output {} B {}".format(
            matching_event, compute_mapping_timings, json_file
        )
    )
    file = compute_mapping_timings
    if os.path.isfile(file):
        try:
            timings = {}
            with open(file, "r") as csvfile:
                timings = csv.reader(csvfile)
                for row in timings:
                    if row[0] == "_GLOBAL":
                        stats["globalTime"] = row[-1]
                    if row[0] == "initialize":
                        stats["initializeTime"] = row[-1]
                    if row[0].startswith("initialize/map") and row[0].endswith(
                        "computeMapping.FromA-MeshToB-Mesh"
                    ):
                        computeMappingName = row[0]
                        # For parallel runs, the primary rank is not included in the comparison and we need to compare explicitly
                        stats["computeMappingTime"] = max(row[5], row[-1])
        except BaseException:
            pass

    # second, generate the correct timings file for the mapData event
    map_data_timings = os.path.join(dir, "timings-mapData.csv")
    matching_event = find_exact_event_name(
        json_file, r'advance[^"]*mapData\.FromA-MeshToB-Mesh'
    )

    os.system(
        "precice-profiling analyze --event {} --output {} B {}".format(
            matching_event, map_data_timings, json_file
        )
    )
    file = map_data_timings
    if os.path.isfile(file):
        try:
            timings = {}
            with open(file, "r") as csvfile:
                timings = csv.reader(csvfile)
                for row in timings:
                    if row[0].startswith("advance/map") and row[0].endswith(
                        "mapData.FromA-MeshToB-Mesh"
                    ):
                        mapDataName = row[0]
                        stats["mapDataTime"] = max(row[5], row[-1])
        except BaseException:
            pass
    return stats


def memoryStats(dir):
    stats = {}
    assert os.path.isdir(dir)
    for P in "A", "B":
        memfile = os.path.join(dir, f"memory-{P}.log")
        total = 0
        if os.path.isfile(memfile):
            try:
                with open(memfile, "r") as file:
                    total = sum([float(e) / 1.0 for e in file.readlines()])
            except BaseException:
                pass
        stats[f"peakMem{P}"] = total

    return stats


def main(argv):
    args = parseArguments(argv[1:])

    globber = os.path.join(args.outdir, "**", "*.stats.json")
    statFiles = [
        os.path.relpath(path, args.outdir)
        for path in glob.iglob(globber, recursive=True)
    ]
    allstats = []
    fields = []
    for file in statFiles:
        print("Found: " + file)
        casedir = os.path.join(args.outdir, os.path.dirname(file))
        parts = os.path.normpath(file).split(os.sep)
        assert len(parts) >= 5
        mapping, constraint, meshes, ranks, _ = parts[-5:]
        meshA, meshB = meshes.split("-")
        ranksA, ranksB = ranks.split("-")

        with open(os.path.join(args.outdir, file), "r") as jsonfile:
            stats = json.load(jsonfile)
            stats["mapping"] = mapping
            stats["constraint"] = constraint
            stats["mesh A"] = meshA
            stats["mesh B"] = meshB
            stats["ranks A"] = ranksA
            stats["ranks B"] = ranksB
            stats.update(statsFromTimings(casedir))
            stats.update(memoryStats(casedir))
            allstats.append(stats)
            if not fields:
                fields += stats.keys()

    assert fields
    writer = csv.DictWriter(args.file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(allstats)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
