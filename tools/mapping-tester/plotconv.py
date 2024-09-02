#! /usr/bin/env python3

import argparse
import itertools
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas
import seaborn as sns


def parseArguments(args):
    parser = argparse.ArgumentParser(
        description="Creates convergence plots from gathered stats"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        default="stats.csv",
        help="The CSV file containing the gathered stats.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        default="result",
        help="The prefix for all generated PDF plots.",
    )
    return parser.parse_args(args)


def lavg(l):
    return math.exp(sum(map(math.log, l)) / len(l))


# seaborn.color_palette("colorblind", 10).as_hex()
style_colours = [
    "#0173b2",
    "#de8f05",
    "#029e73",
    "#d55e00",
    "#cc78bc",
    "#ca9161",
    "#fbafe4",
    "#949494",
    "#ece133",
    "#56b4e9",
]
style_markers = ["o", "D", "s"]
styles = [(c, m) for m in style_markers for c in style_colours]


def determineXAxis(df):
    if df["mesh A"].nunique() == 1 and df["ranks B"].nunique() > 1:
        return "ranks B", "ranks of participant B", False
    else:
        return "mesh A", "edge length(h) of mesh A", True


def plotConv(ax, df, yname, xaxis):
    xmin = df[xaxis].min()
    xmax = df[xaxis].max()
    ymin = df[yname].min()
    ymax = df[yname].max()

    if xmin != xmax:
        # 1st order line
        fox = [xmin, xmax]
        foy1 = ymax
        foy2 = foy1 * (fox[1] / fox[0])
        foy = [foy1, foy2]
        ax.axline(
            (fox[0], foy[0]),
            (fox[1], foy[1]),
            color="lightgray",
            linewidth=1.0,
            zorder=-1,
        )
        ax.annotate("1st order", xy=(lavg(fox), lavg(foy)), color="gray", zorder=-1)


def plotError(df, prefix, xaxis, xlabel, invert_xaxis):
    yname = "relative-l2"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x=xaxis,
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel("relative-l2 error mapping to mesh B")

    plotConv(ax, df, yname, xaxis)

    if invert_xaxis:
        plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-error.pdf")


def plotMemory(df, prefix, xaxis, xlabel, invert_xaxis):
    yname = "peakMemB"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x=xaxis,
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel("peak memory of participant B [Kbytes]")

    # plotConv(ax, df, yname, xaxis)

    if invert_xaxis:
        plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-peakMemB.pdf")


def plotComputeMappingTime(df, prefix, xaxis, xlabel, invert_xaxis):
    yname = "computeMappingTime"
    fig, ax = plt.subplots(sharex=True, sharey=True)
    series = df.groupby("mapping")
    for grouped, style in zip(series, styles):
        name, group = grouped
        if group[yname].max() == 0:
            print(f"Dropping {yname}-series {name} as all 0")
            continue
        color, marker = style
        group.plot(
            ax=ax,
            loglog=True,
            x=xaxis,
            y=yname,
            label=name,
            marker=marker,
            color=color,
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("time to compute mapping [us]")

    # plotConv(ax, df, yname, xaxis)
    if invert_xaxis:
        plt.gca().invert_xaxis()
    plt.grid()
    plt.savefig(prefix + "-computet.pdf")


def plotMapDataTime(df, prefix, xaxis, xlabel, invert_xaxis):
    ynames = ["mapDataTime", "evaluateCacheTime", "updateCacheTime"]
    markers = ["o", "s", "D"]  # Define different markers for each yname
    linestyles = ["-", "--", "-."]  # Define different line styles for each yname
    color_palette = sns.color_palette(
        "colorblind", len(df["mapping"].unique())
    )  # Get the colorblind palette

    fig, ax = plt.subplots(sharex=True, sharey=True)

    colors = {}  # To store the color for each 'mapping'
    series = df.groupby("mapping")

    for idx, (name, group) in enumerate(series):
        if name not in colors:
            colors[name] = color_palette[
                idx
            ]  # Assign a color from the seaborn colorblind palette

        for yname, marker, linestyle in zip(ynames, markers, linestyles):
            if yname not in group.columns or group[yname].max() == 0:
                print(
                    f"Skipping {yname} for series {name} as it does not exist or all values are 0."
                )
                continue

            group.plot(
                ax=ax,
                loglog=True,
                x=xaxis,
                y=yname,
                label=f"{name}",  # Use series name for label (only once in legend)
                marker=marker,
                linestyle=linestyle,
                color=colors[name],  # Ensure consistent color for the same 'mapping'
                legend=False,  # Turn off automatic legend handling
            )

    # Create the first legend for the series name and color mapping
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))  # Remove duplicates
    legend1 = ax.legend(
        unique_labels.values(),
        unique_labels.keys(),
        title="Series",
        loc="upper left",
        bbox_to_anchor=(0, 1),
        borderaxespad=0.0,
    )

    # Create the second legend for the time types with markers and line styles
    marker_lines = [
        plt.Line2D(
            [0],
            [0],
            color="black",
            marker=markers[i],
            linestyle=linestyles[i],
            label=ynames[i],
        )
        for i in range(len(ynames))
    ]
    legend2 = ax.legend(
        handles=marker_lines,
        title="Event",
        loc="upper left",
        bbox_to_anchor=(0.3, 1),
        borderaxespad=0.0,
    )

    # Add the first legend back
    ax.add_artist(legend1)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("time to map Data [us]")

    if invert_xaxis:
        plt.gca().invert_xaxis()

    plt.grid()
    plt.savefig(prefix + "-mapt.pdf")


def plotSummedTimes(df, prefix, xaxis, xlabel, invert_xaxis):
    # Events to sum
    compute_time = "computeMappingTime"
    map_data_time = "mapDataTime"
    evaluate_cache_time = "evaluateCacheTime"
    update_cache_time = "updateCacheTime"

    # Define markers and linestyles
    markers = ["o", "s"]  # Different markers for different sums
    linestyles = ["-", "--"]  # Different line styles for different sums

    # Prepare the color palette
    color_palette = sns.color_palette("colorblind", len(df["mapping"].unique()))

    fig, ax = plt.subplots(sharex=True, sharey=True)

    colors = {}  # To store the color for each 'mapping'
    series = df.groupby("mapping")

    for idx, (name, group) in enumerate(series):
        if name not in colors:
            colors[name] = color_palette[
                idx
            ]  # Assign a color from the seaborn colorblind palette

        # Compute the sum of computeMappingTime + mapDataTime
        if compute_time in group.columns and map_data_time in group.columns:
            group["sum_compute_mapData"] = group[compute_time] + group[map_data_time]
            group.plot(
                ax=ax,
                loglog=True,
                x=xaxis,
                y="sum_compute_mapData",
                label=f"{name}",  # Use series name for label (only once in legend)
                marker=markers[0],
                linestyle=linestyles[0],
                color=colors[name],
                legend=False,
            )

        # Compute the sum of computeMappingTime + evaluateCacheTime + updateCacheTime
        if (
            compute_time in group.columns
            and evaluate_cache_time in group.columns
            and update_cache_time in group.columns
        ):
            group["sum_compute_cache"] = (
                group[compute_time]
                + group[evaluate_cache_time]
                + group[update_cache_time]
            )
            group.plot(
                ax=ax,
                loglog=True,
                x=xaxis,
                y="sum_compute_cache",
                label=f"{name}",  # Use series name for label (only once in legend)
                marker=markers[1],
                linestyle=linestyles[1],
                color=colors[name],
                legend=False,
            )

    # Create the first legend for the series name and color mapping
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))  # Remove duplicates
    legend1 = ax.legend(
        unique_labels.values(),
        unique_labels.keys(),
        title="Series",
        loc="upper left",
        bbox_to_anchor=(0, 1),
        borderaxespad=0.0,
    )

    # Create the second legend for the sum types with markers and line styles
    sum_lines = [
        plt.Line2D(
            [0],
            [0],
            color="black",
            marker=markers[i],
            linestyle=linestyles[i],
            label=f"{'Compute + MapData' if i == 0 else 'Compute + Cache'}",
        )
        for i in range(len(markers))
    ]
    legend2 = ax.legend(
        handles=sum_lines,
        title="Sum Type",
        loc="upper left",
        bbox_to_anchor=(0.25, 1),
        borderaxespad=0.0,
    )

    # Add the first legend back
    ax.add_artist(legend1)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Summed Time [us]")

    if invert_xaxis:
        plt.gca().invert_xaxis()

    plt.grid()
    plt.savefig(prefix + "-summed-times.pdf")


def main(argv):
    args = parseArguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    toMeshes = df["mesh B"].unique()
    assert (
        len(toMeshes) == 1
    ), f"There are {len(toMeshes)} to-meshes but only 1 is allowed."

    xaxis, xlabel, invert_xaxis = determineXAxis(df)

    df.sort_values(xaxis, inplace=True)
    plotError(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotMemory(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotMapDataTime(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotComputeMappingTime(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotSummedTimes(df, args.prefix, xaxis, xlabel, invert_xaxis)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
