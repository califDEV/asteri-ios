#!/usr/bin/env python3
"""Use upstream animation review on CI-exported PNGs and ffprobe timestamps.

No local ffmpeg is needed; the original frames/timestamps are retained unchanged.
Requires Pillow, available in the development host's bundled Python runtime.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import animation_sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames', type=Path)
    parser.add_argument('timestamps', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--scale', type=float, default=3.0)
    parser.add_argument('--start', type=float)
    parser.add_argument('--end', type=float)
    parser.add_argument('--crop', help='X,Y,W,H in points')
    parser.add_argument('--tile-width', type=int, default=300)
    args = parser.parse_args()
    paths = sorted(args.frames.glob('*.png'))
    times = [float(f['best_effort_timestamp_time']) for f in json.loads(args.timestamps.read_text())['frames']]
    if len(paths) != len(times) or not paths:
        raise ValueError('Original PNG count must match ffprobe timestamps')
    if args.scale <= 0 or args.output.exists():
        raise ValueError('Use a positive scale and a fresh output directory')
    crop = tuple(float(v) for v in args.crop.split(',')) if args.crop else None
    frames = []
    args.output.mkdir(parents=True)
    scaled = args.output / 'frames'
    scaled.mkdir()
    for index, (path, time) in enumerate(zip(paths, times)):
        if (args.start is not None and time < args.start) or (args.end is not None and time > args.end):
            continue
        with Image.open(path) as original:
            image = original.convert('RGB')
            if crop:
                x, y, w, h = [round(v * args.scale) for v in crop]
                image = image.crop((x, y, x + w, y + h))
            image = image.resize((round(image.width / args.scale), round(image.height / args.scale)), Image.Resampling.LANCZOS)
            target = scaled / f'{index:05d}.png'
            image.save(target)
            frames.append((str(target), time))
    if not frames:
        raise ValueError('No frames in the selected time range')
    rows = animation_sheet.measure(frames)
    median = animation_sheet.flag(rows)
    sheets = animation_sheet.sheets(frames, rows, str(args.output), 4, 3, args.tile_width, [])
    animation_sheet.chart(rows, median, str(args.output))
    with (args.output / 'frames.tsv').open('w', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t')
        writer.writerow(['index', 'time_s', 'interval_ms', 'change', 'to_final', 'changed_region', 'flags'])
        for row in rows:
            writer.writerow([row['index'], row['time'], row['interval'], row['change'], row['to_final'], row['region'], ','.join(row['flags'])])
    summary = {'frames': len(frames), 'first_time': frames[0][1], 'last_time': frames[-1][1],
               'median_motion_interval_ms': median, 'sheets': sheets,
               'flagged': [{k: row[k] for k in ('index', 'time', 'interval', 'flags')} for row in rows if row['flags']]}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
