import joblib, json, glob

# Check production artifact validation_metrics structure
prod = joblib.load('data/models/xauusd_xgboost-20260919T002001Z-production.joblib')
meta = prod.get('metadata', {})
wf = meta.get('validation_metrics', {})
print('VALIDATION_METRICS type:', type(wf))
print('VALIDATION_METRICS keys:', list(wf.keys()) if isinstance(wf, dict) else 'list with %d items' % len(wf))
if isinstance(wf, dict):
    print(json.dumps(wf, indent=2, default=str)[:600])

print("\n=== Per-candidate summary ===")
for h in [1, 2, 4]:
    for model in ['logistic_regression', 'random_forest', 'xgboost', 'lightgbm']:
        files = sorted(glob.glob(f'data/models/xauusd_{model}-*20260919*-candidate_h{h}.joblib'))
        for f in files[-1:]:
            art = joblib.load(f)
            meta2 = art.get('metadata', {})
            ftm = meta2.get('final_test_metrics')
            wf_m = meta2.get('validation_metrics')
            if ftm:
                acc = ftm.get('accuracy', 0)
                roc = ftm.get('roc_auc_ovr_weighted', 0)
                print(f'{model} {h}H: holdout_acc={acc:.4f}, roc={roc:.4f}, wf_type={type(wf_m).__name__}')
            else:
                print(f'{model} {h}H: NO final_test_metrics in {f}')

# Also check the 3rd run's candidates (20260919T001xxx vs 20260919T002xxx)
print("\n=== All 20260919 production/candidate files ===")
for f in sorted(glob.glob('data/models/xauusd_*20260919*.joblib')):
    art = joblib.load(f)
    meta3 = art.get('metadata', {})
    ftm = meta3.get('final_test_metrics')
    tag = meta3.get('artifact_tag', '?')
    model = meta3.get('model', '?')
    h = meta3.get('target_horizon', '?')
    acc = ftm.get('accuracy', 0) if ftm else 0
    print(f'{f.split(chr(92))[-1]}: model={model}, h={h}, acc={acc:.4f}')
