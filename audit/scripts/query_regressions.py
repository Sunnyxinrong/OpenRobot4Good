"""Constructed regressions, not dataset defects or empirical error rates."""
import json
from reproduce import ROOT,REQUIREMENTS,query_claim
from test_audit import SCOPE,row

def legacy_missing(records,claim):
    mapping={'license':'data_license','actual_file':'retrieved_file','semantic_mapping':'semantic_mapping','implemented_adapter':'implemented_adapter','target_evaluation':'target_evaluation'}
    observed=set();blocked=set()
    for r in records:
        if r['dataset_id']!=SCOPE['dataset_id'] or r['indicator'] not in mapping:continue
        key=mapping[r['indicator']]
        if r['state']=='conflicting':blocked.add(key)
        if r['state']=='documented' and r['value'] not in (None,False,''):observed.add(key)
    return sorted(REQUIREMENTS[claim]-(observed-blocked))

def main():
    cases=[('different_revision','file_access',[row('license'),row('actual_file',revision='r2')],['retrieved_file']),('different_subset','file_access',[row('license',subset='B'),row('actual_file')],['data_license']),('different_context','cross_robot_transfer',[row('semantic_mapping'),row('implemented_adapter'),row('target_evaluation',context_id='run2')],['target_evaluation'])]
    for claim in ['worker_welfare','energy_per_success','operational_carbon']:
        cases.append(('complete_'+claim,claim,[row(k) for k in sorted(REQUIREMENTS[claim])],[]))
    cases.append(('same_scope_access','file_access',[row('license'),row('actual_file')],[]))
    results=[]
    for name,claim,records,expected in cases:
        revised=query_claim(records,claim,SCOPE);old=legacy_missing(records,claim)
        assert revised['missing']==expected,(name,revised)
        results.append(dict(case=name,claim=claim,expected_missing=expected,legacy_missing=old,revised_missing=revised['missing'],legacy_matches_expectation=old==expected,revised_matches_expectation=True,fixture_records=records))
    output=dict(scope='Seven constructed cases; no empirical error-rate estimate',legacy_cases_matching=sum(x['legacy_matches_expectation'] for x in results),revised_cases_matching=len(results),cases=results)
    (ROOT/'results/query_regressions.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print('Constructed cases: legacy',output['legacy_cases_matching'],'/ 7; revised 7 / 7.')

if __name__=='__main__':main()
