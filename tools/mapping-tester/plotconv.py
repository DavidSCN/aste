#! /usr/bin/env python3

import argparse
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas


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
    import tikzplotlib

    tikzplotlib.save("error.tex")
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
    import tikzplotlib

    tikzplotlib.save("memory.tex")
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
    import tikzplotlib

    tikzplotlib.save("computet.tex")
    plt.savefig(prefix + "-computet.pdf")


def plotMapDataTime(df, prefix, xaxis, xlabel, invert_xaxis):
    yname = "mapDataTime"
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
    ax.set_ylabel("time to map Data [us]")

    # plotConv(ax, df, yname, xaxis)
    if invert_xaxis:
        plt.gca().invert_xaxis()
    plt.grid()
    import tikzplotlib

    tikzplotlib.save("mapt.tex")
    plt.savefig(prefix + "-mapt.pdf")


def main(argv):
    args = parseArguments(argv[1:])

    plt.rcParams["legend.fontsize"] = "small"
    plt.rcParams["figure.figsize"] = "8, 8"
    plt.rcParams["figure.autolayout"] = "true"

    df = pandas.read_csv(args.file)
    # toMeshes = df["mesh B"].unique()
    # assert (
    #     len(toMeshes) == 1
    # ), f"There are {len(toMeshes)} to-meshes but only 1 is allowed."
    xaxis, xlabel, invert_xaxis = determineXAxis(df)

    df.sort_values(xaxis, inplace=True)
    plotError(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotMemory(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotMapDataTime(df, args.prefix, xaxis, xlabel, invert_xaxis)
    plotComputeMappingTime(df, args.prefix, xaxis, xlabel, invert_xaxis)
    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
