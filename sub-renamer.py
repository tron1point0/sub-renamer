#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path
from typing import Iterable, Set, Dict

MOVIE_EXTENSIONS = {
        ".avi",
        ".mkv",
        ".mp4",
        ".ts",
        }

SUBTITLE_GLOBS = [
        "Subs/*.srt",
        "Subs/*.sub",
        "Subs/*.idx",
        ]

# 300 MB
MIN_MOVIE_SIZE = 300 * 1024 * 1024


def usage() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
            description="Move and rename subtitle files so Jellyfin can pick them up",
            epilog=""
            )
    a.add_argument(
            "--all-movies",
            nargs="?",
            default=[],
            const=Path("."),
            action="append",
            type=Path,
            help="Directory containing several movie directories that will be "
            "processed with --movie. You can use this format to process "
            "everything in the movie directory all at once. If no value "
            "is given, this assumes the current directory."
            )
    a.add_argument(
            "--movie",
            nargs="?",
            default=[],
            const=Path("."),
            action="append",
            type=Path,
            help="Directory containing a movie and subtitle files to process. "
            "You can use this to process a single movie that was just "
            "downloaded. If no value is given, this assumes the current "
            "directory."
            )
    a.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Don't actually rename the files. Just print out what files "
            "would be renamed instead."
            )
    return a


def find_movie(movie_folder: Path) -> Path:
    """Finds the _only_ movie file in the directory at `path`.

    If there are multiple files which could be "the" movie, this method throws
    an exception.
    """
    def is_movie(file: Path) -> bool:
        return file.suffix in MOVIE_EXTENSIONS \
                and file.stat().st_size > MIN_MOVIE_SIZE

    movies = [f for f in movie_folder.iterdir() if is_movie(f)]

    if not movies:
        raise RuntimeError(f"Did not find any movies in {movie_folder}")

    if len(movies) > 1:
        raise RuntimeError(f"Found more than one movie in {movie_folder}")

    return movies[0]


def find_subs(movie_folder: Path) -> Set[Path]:
    """Finds all the subtitle files in the movie's `Subs/` folder.

    This returns *all* such files. If none are found, it returns the empty list.
    """
    results = set()
    for g in SUBTITLE_GLOBS:
        for f in movie_folder.glob(g):
            results.add(f)
    return results


def sub_renames(movie: Path, sub_files: Iterable[Path]) -> Dict[Path, Path]:
    """Returns a mapping from the old name of each subtitle file to the new name
    for passing through `rename`.

    Examples:
        >>> sub_renames(
        ...     Path("a/Movie.Name.mkv"),
        ...     [Path("a/Subs/2_English.srt"), Path("a/Subs/3_French.srt")]
        ...     )
        {PosixPath('a/Subs/2_English.srt'): PosixPath('a/Movie.Name.2_English.srt'),
         PosixPath('a/Subs/3_French.srt'): PosixPath('a/Movie.Name.3_French.srt')}
    """
    def rename_with(sub_file: Path) -> Path:
        return movie.parent / (movie.stem + "." + sub_file.stem + sub_file.suffix)

    return {sub: rename_with(sub) for sub in sub_files}


def rename_single_movie_dir(directory: Path, args):
    """Handle a single movie directory."""
    movie = find_movie(directory)
    subs = find_subs(directory)
    renames = sub_renames(movie, subs)

    for k, v in renames.items():
        print(f"{k} -> {v}")
        if not args.dry_run:
            k.rename(v)


def main():
    args = usage().parse_args()

    if not args.all_movies and not args.movie:
        usage().print_help()
        exit(1)

    for container in args.all_movies:
        for directory in container.iterdir():
            if directory.is_dir():
                try:
                    rename_single_movie_dir(directory, args)
                except RuntimeError as e:
                    print(e, file=sys.stderr)

    for movie in args.movie:
        rename_single_movie_dir(movie, args)


if __name__ == "__main__":
    main()

