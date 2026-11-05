"""Check delivery integrity without rendering, fitting, or changing predictions."""
from pathlib import Path
import ast
import hashlib
import json
import re

PAIR = Path(__file__).resolve().parents[1]
PARENT = PAIR.parents[1]


def load(path):
    def reject(value):
        raise ValueError(f"Nonstandard JSON number in {path}: {value}")
    return json.loads(Path(path).read_text(), parse_constant=reject)


def check_files(records):
    for record in records:
        path = Path(record['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path
    return len(records)


def main():
    report = {}
    report['prior_files_unchanged_N'] = check_files(
        load(PAIR / 'assets_index/PRIOR_EXPERIMENT_FREEZE.json')['files'])
    assert report['prior_files_unchanged_N'] == 149
    report['local_data_files_unchanged_N'] = check_files(
        load(PAIR / 'assets_index/LOCAL_DATA_INDEX.json')['files'])
    for entry in load(PAIR / 'assets_index/ALGORITHM_REUSE.json')['identical_files']:
        a = (PARENT / 'code' / entry['name']).read_bytes()
        b = (PAIR / 'code' / entry['name']).read_bytes()
        assert a == b
        assert hashlib.sha256(b).hexdigest() == entry['copy_sha256']
    report['case_checks'] = []
    for name in ['A_expansion', 'B_contraction']:
        root = PAIR / 'cases' / name
        implementation_N = check_files(load(root / 'metrics/IMPLEMENTATION_FREEZE.json')['files'])
        prediction_N = check_files(load(root / 'metrics/PREDICTION_FREEZE.json')['files'])
        assert load(root / 'metrics/FIT_START.json')['GT_firewall_pass']
        assert load(root / 'metrics/FIT_START.json')['holdout_not_in_loss']
        assert load(root / 'metrics/PROJECTION_GATE.json')['passed']
        assert load(root / 'metrics/BLENDER_PHYSICAL_AUDIT.json')['passed']
        evaluation = load(root / 'metrics/GEOMETRY_EVALUATION.json')
        for stage in evaluation['stages']:
            assert stage['fixed_surface_N'] == 11374
            assert stage['quality']['closed'] and stage['quality']['components'] == 1
            assert not stage['Ring']['triangle_collision']
        diagnostic = load(root / 'metrics/GT_OBJECTIVE_DIAGNOSTIC.json')
        assert diagnostic['prediction_frozen_before_GT_substitution']
        assert diagnostic['no_new_optimizer_or_parameter_search']
        assert abs(diagnostic['final_loss'] - load(root / 'metrics/FIT_FINISHED.json')['loss']) < 1e-12
        if name == 'A_expansion':
            assert not evaluation['gates']['physical_peak']
            assert not evaluation['all_numeric_gates_pass']
        else:
            assert evaluation['all_numeric_gates_pass']
            assert load(root / 'metrics/VOLUME_VALIDATION.json')['genuine_volume_deletion']
        report['case_checks'].append(dict(case=name, implementation_files_N=implementation_N,
                                         prediction_files_N=prediction_N,
                                         projection_and_physical_checks_pass=True))
    syntax = list((PAIR / 'code').rglob('*.py'))
    for path in syntax:
        ast.parse(path.read_text(), filename=str(path))
    report['python_syntax_files_N'] = len(syntax)
    json_files = [path for path in PAIR.rglob('*.json') if 'runtime' not in path.parts]
    for path in json_files:
        load(path)
    report['strict_JSON_files_N'] = len(json_files)
    for path in PAIR.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent / target.split('#')[0]).exists(), (path, target)
    figures = sorted((PAIR / 'figures').glob('Fig*.png'))
    assert len(figures) == 4
    for path in figures:
        assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        assert path.stat().st_size < 4 * 1024 * 1024
    acceptance = load(PAIR / 'ACCEPTANCE.json')
    assert acceptance['stopped'] and not acceptance['both_accurate']
    assert not acceptance['scientific_generalization']
    report.update(passed=True, predictions_changed=False, extra_optimization=False,
                  scientific_result='MIXED_A_UNDER_EXPANSION_B_PASS')
    output = PAIR / 'assets_index/DELIVERY_VALIDATION.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
