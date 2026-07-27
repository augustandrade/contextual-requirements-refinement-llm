#!/usr/bin/env python3
import json
from pathlib import Path
import csv

_HERE = Path(__file__).parent
OUT_DIR = _HERE.parent / 'outputs'


def scan_outputs(out_dir: Path):
    report = {
        'total_executions': 0,
        'by_status': {},
        'requirements': {},
        'extra_dirs': []
    }

    for req_dir in sorted(out_dir.iterdir()):
        if not req_dir.is_dir():
            continue
        req_id = req_dir.name
        report['requirements'][req_id] = {}
        for ctx_dir in sorted(req_dir.iterdir()):
            if not ctx_dir.is_dir():
                continue
            ctx = ctx_dir.name
            report['total_executions'] += 1
            res_file = ctx_dir / '03_resolubility_validation.json'
            struct_file = ctx_dir / '04_requirement_structuring.json'
            status = 'missing'
            final_output_status = None
            if res_file.exists():
                try:
                    r = json.loads(res_file.read_text(encoding='utf-8'))
                    status = r.get('contextual_resolubility_validation', {}).get('overall_resolubility', {}).get('status', 'unknown')
                except Exception as e:
                    status = f'error:{e}'
            if struct_file.exists():
                try:
                    s = json.loads(struct_file.read_text(encoding='utf-8'))
                    final_output_status = s.get('requirement_structuring', {}).get('final_output_status')
                except Exception:
                    final_output_status = None

            report['requirements'][req_id][ctx] = {
                'resolubility_status': status,
                'final_output_status': final_output_status
            }

            report['by_status'].setdefault(status, 0)
            report['by_status'][status] += 1

    return report


def save_report(report, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))

    # CSV flat list
    csv_path = out_dir / 'report.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['requirement_id', 'context', 'resolubility_status', 'final_output_status'])
        for req_id, ctxs in sorted(report['requirements'].items()):
            for ctx, v in sorted(ctxs.items()):
                writer.writerow([req_id, ctx, v.get('resolubility_status'), v.get('final_output_status')])


def main():
    report = scan_outputs(OUT_DIR)
    save_report(report, OUT_DIR)
    print('Report saved to', OUT_DIR)


if __name__ == '__main__':
    main()
