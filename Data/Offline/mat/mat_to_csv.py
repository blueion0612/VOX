#!/usr/bin/env python3
"""
mat_to_csv.py

Convert 6DMG .mat files for V, X, O gestures into a single CSV with labels:
  V → 0, X → 1, O → 2.
Uses the preprocessed acceleration and angular speed data provided (no additional Listing 1 transforms).

Usage:
    python mat_to_csv.py [--folders 폴더1 폴더2 ...] [--out 출력경로.csv]

Requirements:
    pip install numpy scipy pandas
"""
import os
import re
import argparse
import scipy.io
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description='Generate CSV for V/X/O gestures from 6DMG .mat files'
    )
    parser.add_argument(
        '--folders', nargs='+',
        default=['mat/matL', 'mat/matR'],
        help='Search these folders for .mat files'
    )
    parser.add_argument(
        '--out', default='6DMG_VXO.csv',
        help='Output CSV filename'
    )
    args = parser.parse_args()

    pattern = re.compile(r'g(\d{2})_([A-Za-z0-9]+)_t(\d{2})\.mat$', re.IGNORECASE)
    # label_map = {12:0, 13:1, 14:2, 15:2, 16:2, 17:2}
    label_map = {12:0, 13:1, 17:2}


    channel_cols = [
        'timestamp',          # ms
        'pos_x', 'pos_y', 'pos_z',
        'ori_w', 'ori_x', 'ori_y', 'ori_z',
        'acc_x', 'acc_y', 'acc_z',
        'w_yaw', 'w_pitch', 'w_roll'
    ]

    records = []
    for folder in args.folders:
        if not os.path.isdir(folder):
            print(f'⚠️ Folder not found, skipping: {folder}')
            continue
        for root, _, files in os.walk(folder):
            for fname in files:
                if not fname.lower().endswith('.mat'):
                    continue
                m = pattern.match(fname)
                if not m:
                    print(f'  • Skipping name mismatch: {fname}')
                    continue
                g_id = int(m.group(1))
                if g_id not in label_map:
                    continue
                label = label_map[g_id]
                user_id = m.group(2)
                trial_id = int(m.group(3))

                data = scipy.io.loadmat(os.path.join(root, fname))
                gest = data['gest']    # (14, n), already transformed

                # Directly use provided data without reapplying Listing 1 transforms
                df = pd.DataFrame(gest.T, columns=channel_cols)
                # timestamp ms -> seconds
                df['timestamp'] = df['timestamp'] / 1000.0

                # Meta info
                df['gesture_id'] = g_id
                df['user_id']    = user_id
                df['trial_id']   = trial_id
                df['label']      = label
                df['source']     = fname

                records.append(df)

    if not records:
        print('❌ No .mat files found. Check paths and pattern.')
        return

    full_df = pd.concat(records, ignore_index=True)
    full_df.to_csv(args.out, index=False)
    print(f'✅ Saved CSV: {args.out}')
    print(f'   Total samples row count: {len(full_df)}, Files processed: {len(records)}')


if __name__ == '__main__':
    main()