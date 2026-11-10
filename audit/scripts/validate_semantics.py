"""Check the pinned Panda Threading action-map transcription, not physical control.

The reference is separately written below rather than inferred from array width.
Both reference and parser remain AI-assisted; this is NOT independent human or
controller validation. Hash-bound publisher metadata is copied into data/.
"""
import copy,hashlib,json
from reproduce import ROOT

REFERENCE={
 'left_arm_eef_pos':(0,3,False,None),
 'left_arm_eef_rot':(3,6,False,'axis_angle'),
 'left_gripper_close':(6,7,None,None),
 'right_arm_eef_pos':(7,10,False,None),
 'right_arm_eef_rot':(10,13,False,'axis_angle'),
 'right_gripper_close':(13,14,None,None),
}

def verify_map(mapping):
    if set(mapping)!=set(REFERENCE):return False
    used=[]
    for name,(start,end,absolute,rotation) in REFERENCE.items():
        part=mapping[name]
        if (part.get('start'),part.get('end'),part.get('absolute'),part.get('rotation_type'))!=(start,end,absolute,rotation):return False
        if 'gripper' in name and part.get('dtype')!='int64':return False
        used.extend(range(start,end))
    return sorted(used)==list(range(14)) and len(set(used))==14

def main():
    probes=json.loads((ROOT/'data/file_probes.json').read_text(encoding='utf-8'))
    probe=next(p for p in probes if p['dataset_id']=='grootsim')
    path=ROOT/'data/pinned/grootsim_modality.json'
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==probe['modality']['sha256']
    assert len(raw)==probe['modality']['bytes']
    mapping=json.loads(raw)['action']
    assert verify_map(mapping)
    mutations=[]
    swapped=copy.deepcopy(mapping)
    for suffix in ('arm_eef_pos','arm_eef_rot','gripper_close'):
        swapped['left_'+suffix],swapped['right_'+suffix]=swapped['right_'+suffix],swapped['left_'+suffix]
    mutations.append(('swapped_arm_slices',swapped))
    absolute=copy.deepcopy(mapping);absolute['left_arm_eef_pos']['absolute']=True
    mutations.append(('relative_as_absolute',absolute))
    euler=copy.deepcopy(mapping);euler['left_arm_eef_rot']['rotation_type']='euler_angles'
    mutations.append(('axis_angle_as_euler',euler))
    rows=[]
    for name,mutated in mutations:
        assert not verify_map(mutated)
        rows.append(dict(case=name,array_changed=False,width_null_finite_checks_would_change=False,reference_check_rejects=True))
    output=dict(dataset_id='grootsim',revision=probe['revision'],subset='bimanual_panda_gripper.Threading',
        source_url=probe['modality']['url'],sha256=probe['modality']['sha256'],
        check='publisher transcription and exact index coverage only',channels_covered=14,components=6,
        reference_check_passed=True,mutations=rows,
        unresolved=['translation units','reference frame','rotation composition and scaling','controller gains','gripper polarity on a target','action-observation timing'],
        independent_human_or_controller_validation=False,target_transfer_validated=False)
    (ROOT/'results/semantic_validation.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print('Pinned map: six components cover 14 indices; three constructed semantic mutations rejected; target transfer unvalidated.')

if __name__=='__main__':main()
