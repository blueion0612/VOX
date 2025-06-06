#!/usr/bin/env python3
import os
import scipy.io
import csv

def check_mat_file(filepath):
    try:
        data = scipy.io.loadmat(filepath)
        gest = data.get('gest')
        bias = data.get('bias')
        noise = data.get('noise')
        return {
            'file': filepath,
            'has_gest': bool(gest is not None),
            'gest_rows': gest.shape[0] if gest is not None else '',
            'gest_cols': gest.shape[1] if gest is not None else '',
            'has_bias': bool(bias is not None),
            'bias_shape': bias.shape if bias is not None else '',
            'has_noise': bool(noise is not None),
            'noise_shape': noise.shape if noise is not None else '',
            'error': ''
        }
    except Exception as e:
        return {
            'file': filepath,
            'has_gest': False,
            'gest_rows': '',
            'gest_cols': '',
            'has_bias': False,
            'bias_shape': '',
            'has_noise': False,
            'noise_shape': '',
            'error': str(e)
        }

def main():
    folders = ['C:/Capstone/arm-pose-estimation-main/mat/matL', 'C:/Capstone/arm-pose-estimation-main/mat/matR']
    records = []
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"경고: '{folder}' 폴더를 찾을 수 없습니다.")
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith('.mat'):
                path = os.path.join(folder, fname)
                records.append(check_mat_file(path))

    # CSV로 저장
    csv_file = 'mat_feature_check.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'file',
            'has_gest', 'gest_rows', 'gest_cols',
            'has_bias', 'bias_shape',
            'has_noise', 'noise_shape',
            'error'
        ])
        for r in records:
            writer.writerow([
                r['file'],
                r['has_gest'], r['gest_rows'], r['gest_cols'],
                r['has_bias'], r['bias_shape'],
                r['has_noise'], r['noise_shape'],
                r['error']
            ])

    print(f"✅ 검사 완료: {len(records)}개 파일을 분석하여 '{csv_file}'에 저장했습니다.")

if __name__ == '__main__':
    main()
