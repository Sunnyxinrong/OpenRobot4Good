"""Rebuild the draft's descriptive results. Python 3.10+, standard library.

Default: offline from source-linked audit records (not redoing the web audit).
--verify-remote: also re-download three pinned files/cards/info, verify their
SHA-256 hashes, and independently re-parse Parquet footers. No data are retained.
--local-probes DIR: verify already downloaded files, named DATASET.parquet.
"""
from pathlib import Path
import argparse,csv,hashlib,json,tempfile
from urllib.request import Request,urlopen
from parquet_footer import inspect

ROOT=Path(__file__).resolve().parents[1]
STATES={'documented','partial','not_located','conflicting','not_applicable','not_assessed'}
REQUIREMENTS={
    'file_access':{'data_license','retrieved_file'},
    'cross_robot_transfer':{'semantic_mapping','implemented_adapter','target_evaluation'},
    'worker_welfare':{'stakeholder','exposure_link','worker_outcome','comparison'},
    'energy_per_success':{'meter_boundary','power_interval','success_rule','attempt_accounting','successful_outputs'},
    'operational_carbon':{'measured_energy','time_location','electricity_factor'},
}
FIELD_MAP={key:key for fields in REQUIREMENTS.values() for key in fields}
FIELD_MAP.update(license='data_license',actual_file='retrieved_file')
SCOPE_FIELDS=('dataset_id','revision','subset','context_id')

def validate_scope(scope):
    # No wildcard or implicit inheritance: broader documents need an explicit,
    # source-justified applicability record for this exact query scope.
    if any(not isinstance(scope.get(k),str) or not scope[k].strip() or scope[k]=='*' for k in SCOPE_FIELDS):
        raise ValueError('Explicit dataset_id, revision, subset and context_id required')
    return {k:scope[k] for k in SCOPE_FIELDS}

def required_evidence(claim,observed):
    missing=sorted(REQUIREMENTS[claim]-set(observed))
    return {'status':'requirements_documented_within_scope' if not missing else 'additional_evidence_required','missing':missing}

def documented_requirements(evidence,query_scope):
    scope=validate_scope(query_scope)
    observed={};blocked=set()
    for row in evidence:
        if any(row.get(k)!=v for k,v in scope.items()) or row['indicator'] not in FIELD_MAP:continue
        requirement=FIELD_MAP[row['indicator']]
        if row['state']=='conflicting':blocked.add(requirement)
        value=row.get('value')
        # Zero is a meaningful measurement. Missing containers/strings are not.
        has_value=value is not None and value is not False and value!='' and value!=[] and value!={}
        if row['state']=='documented' and has_value and row.get('source_url','').startswith('https://') and row.get('locator'):
            observed.setdefault(requirement,[]).append(row['source_url'])
    return {k:v for k,v in observed.items() if k not in blocked}

def query_claim(evidence,claim,query_scope):
    scope=validate_scope(query_scope)
    observed=documented_requirements(evidence,scope)
    result=required_evidence(claim,observed)
    result['query_scope']=scope
    result['supporting_sources']=sorted({url for key,urls in observed.items() if key in REQUIREMENTS[claim] for url in urls})
    result['conflicting_requirements']=sorted({FIELD_MAP[row['indicator']] for row in evidence
        if row.get('indicator') in FIELD_MAP and FIELD_MAP[row['indicator']] in REQUIREMENTS[claim]
        and row.get('state')=='conflicting' and all(row.get(k)==v for k,v in scope.items())})
    return result

def load_records():
    probes=json.loads((ROOT/'data/file_probes.json').read_text(encoding='utf-8'))
    structures=json.loads((ROOT/'data/structures.json').read_text(encoding='utf-8'))
    evidence=json.loads((ROOT/'data/evidence.json').read_text(encoding='utf-8'))
    with (ROOT/'data/screening.csv').open(encoding='utf-8-sig',newline='') as f:screen=list(csv.DictReader(f))
    return probes,structures,evidence,screen

def verify(probes,structures,remote=False,local=None):
    status=[];expected={x['dataset_id']:x for x in structures}
    with tempfile.TemporaryDirectory(prefix='robot-audit-') as td:
        for p in probes:
            sid=p['dataset_id']
            artifacts=[('readme','_readme.md'),('data','.parquet'),('info','_info.json')]
            if 'modality' in p:
                artifacts.append(('modality','_modality.json'))
            for kind,ext in artifacts:
                record=p[kind]
                path=Path(local)/(sid+ext) if local else Path(td)/(sid+ext)
                if remote:
                    with urlopen(Request(record['url'],headers={'User-Agent':'Open-robot-evidence-audit/0.1'}),timeout=60) as r:
                        payload=r.read(25_000_001)
                        if len(payload)>25_000_000:raise ValueError('File exceeds probe cap')
                    path.write_bytes(payload)
                if not path.exists():raise FileNotFoundError(path)
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError(f'Hash mismatch: {sid}/{kind}')
                if len(raw)!=record['bytes']:raise ValueError(f'Byte mismatch: {sid}/{kind}')
                if kind=='data':
                    actual=inspect(path)
                    for field in ['rows','schema','column_paths']:
                        if actual[field]!=expected[sid][field]:raise ValueError(f'Footer mismatch: {sid}/{field}')
                if kind=='info':
                    info=json.loads(raw)
                    if info['features']['action']['shape']!=expected[sid]['declared']['action']['shape']:raise ValueError('Action shape changed')
                if kind=='modality' and json.loads(raw)['action']!=expected[sid]['publisher_action_map']:
                    raise ValueError(f'Action mapping changed: {sid}')
                status.append({'dataset_id':sid,'artifact':kind,'sha256_verified':True})
    return status

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify-remote',action='store_true');ap.add_argument('--local-probes',type=Path);args=ap.parse_args()
    probes,structures,evidence,screen=load_records()
    assert len({x['dataset_id'] for x in screen})==len(screen)
    assert all(x['state'] in STATES and x['source_url'].startswith('https://') and x['scope'] for x in evidence)
    included=[x for x in screen if x['cohort_decision']=='included']
    assert all(x['commercial_permission_documented']=='yes' and x['file_verified']=='yes' for x in included)
    assert {x['dataset_id'] for x in included}=={p['dataset_id'] for p in probes}
    assert all(p['data']['status']==200 and p['parquet_magic'] and len(p['revision'])==40 for p in probes)
    out=ROOT/'results';out.mkdir(exist_ok=True)
    summary={'candidate_resources':len(screen),'unique_included_underlying_resources':len({x['underlying_id'] for x in included}),
             'pending_file_or_scope_verification':sum(x['cohort_decision']=='pending' for x in screen),
             'actual_data_files_retrieved':len(probes),'probe_rows':{x['dataset_id']:x['rows'] for x in structures},
             'declared_action_dimensions':{x['dataset_id']:x['declared']['action']['shape'][0] for x in structures},
             'declared_fps':{x['dataset_id']:x['declared']['fps'] for x in structures},
             'verified_probe_bytes':sum(x['data']['bytes'] for x in probes),
             'claim_scope':'descriptive access/schema pilot; no population prevalence, training, economic, welfare, or carbon estimate'}
    (out/'main_results.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    table=['| Release | Data license | LeRobot | Declared dimensions | Hz | Footer rows | Bytes |','|---|---|---|---:|---:|---:|---:|']
    pmap={x['dataset_id']:x for x in probes};smap={x['dataset_id']:x for x in screen}
    for s in structures:
        sid=s['dataset_id'];d=s['declared'];p=pmap[sid]
        table.append(f"| {smap[sid]['name']} | {smap[sid]['data_license']} | {d['codebase_version']} | {d['action']['shape'][0]} | {d['fps']:g} | {s['rows']:,} | {p['data']['bytes']:,} |")
    (out/'pilot_table.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
    tex=['% Generated from pinned file_probes.json and structures.json; insert into main.tex only after review.']
    for s in structures:
        sid=s['dataset_id'];tex.append(f"{smap[sid]['name']} & {s['declared']['action']['shape'][0]} & {s['declared']['fps']:g} & {s['rows']:,} \\\\")
    (out/'pilot_numbers.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')
    claims=[]
    for s in structures:
        for claim in ['file_access','cross_robot_transfer','worker_welfare','energy_per_success','operational_carbon']:
            query_scope=json.loads((ROOT/'data/query_scopes.json').read_text(encoding='utf-8'))[s['dataset_id']]
            r=query_claim(evidence,claim,query_scope)
            links=r['supporting_sources']
            audit_urls=[pmap[s['dataset_id']][k]['url'] for k in ['readme','info','data']]
            claims.append(dict(**query_scope,claim=claim,status=r['status'],missing_requirements='; '.join(r['missing']),conflicting_requirements='; '.join(r['conflicting_requirements']),supporting_sources='; '.join(links),audited_sources='; '.join(audit_urls),scope='exact release/subset/context; recorded sources only'))
    with (out/'claim_matrix.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(claims[0]));w.writeheader();w.writerows(claims)
    if args.verify_remote or args.local_probes:
        mode='remote' if args.verify_remote else 'local_downloads'
        try:
            checked=verify(probes,structures,args.verify_remote,args.local_probes)
        except Exception as exc:
            failure={'status':'failed','mode':mode,'error':str(exc)}
            (out/'verification.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
            raise
        (out/'verification.json').write_text(json.dumps({'status':'passed','mode':mode,'checks':checked},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
