"""Meaningful checks for evidence gating and malformed binary rejection."""
import tempfile,unittest
from pathlib import Path
from parquet_footer import CompactReader,inspect
from reproduce import REQUIREMENTS,query_claim,required_evidence,load_records

SCOPE=dict(dataset_id='fixture',revision='r1',subset='A',context_id='run1')
def row(indicator,**changes):
    result=dict(**SCOPE,indicator=indicator,state='documented',value='recorded',source_url='https://example.org/'+indicator,locator='fixture only')
    result.update(changes)
    return result

class AuditChecks(unittest.TestCase):
    def test_shape_is_not_transfer(self):
        result=required_evidence('cross_robot_transfer',{'action_shape','file_format','data_license'})
        self.assertEqual(result['status'],'additional_evidence_required')
        self.assertIn('semantic_mapping',result['missing'])
    def test_timestamps_do_not_measure_energy(self):
        result=required_evidence('energy_per_success',{'timestamp','reward','successful_outputs'})
        self.assertIn('meter_boundary',result['missing'])
        self.assertIn('attempt_accounting',result['missing'])
    def test_no_zero_imputation(self):
        _,_,evidence,_=load_records()
        self.assertTrue(all(x['value'] is None for x in evidence if x['state'] in {'not_located','not_assessed'}))
    def test_conflict_blocks_permission_premise(self):
        result=query_claim([row('license'),row('actual_file'),row('license',state='conflicting',value=None)],'file_access',SCOPE)
        self.assertEqual(result['missing'],['data_license'])
        self.assertEqual(result['conflicting_requirements'],['data_license'])
    def test_cross_revision_join_rejected(self):
        result=query_claim([row('license'),row('actual_file',revision='r2')],'file_access',SCOPE)
        self.assertEqual(result['missing'],['retrieved_file'])
    def test_cross_subset_join_rejected(self):
        result=query_claim([row('license',subset='B'),row('actual_file')],'file_access',SCOPE)
        self.assertEqual(result['missing'],['data_license'])
    def test_cross_context_join_rejected(self):
        records=[row(k,context_id='run2' if k=='comparison' else 'run1') for k in REQUIREMENTS['worker_welfare']]
        self.assertEqual(query_claim(records,'worker_welfare',SCOPE)['missing'],['comparison'])
    def test_missing_scope_rejected(self):
        with self.assertRaises(ValueError):query_claim([],'file_access',{'dataset_id':'fixture'})
    def test_unscoped_row_cannot_supply_evidence(self):
        record=row('license');del record['subset']
        self.assertIn('data_license',query_claim([record,row('actual_file')],'file_access',SCOPE)['missing'])
    def test_wildcard_scope_rejected(self):
        with self.assertRaises(ValueError):query_claim([],'file_access',dict(SCOPE,subset='*'))
    def test_every_claim_family_accepts_complete_scoped_evidence(self):
        for claim,fields in REQUIREMENTS.items():
            with self.subTest(claim=claim):
                result=query_claim([row(k) for k in fields],claim,SCOPE)
                self.assertEqual(result['missing'],[])
                self.assertEqual(len(result['supporting_sources']),len(fields))
    def test_unrelated_conflict_does_not_block(self):
        result=query_claim([row('license'),row('actual_file'),row('license',state='conflicting',revision='r2')],'file_access',SCOPE)
        self.assertEqual(result['missing'],[])
    def test_partial_and_source_free_rows_do_not_satisfy(self):
        result=query_claim([row('license',state='partial'),row('actual_file',locator='')],'file_access',SCOPE)
        self.assertEqual(len(result['missing']),2)
    def test_zero_measurement_is_retained(self):
        result=query_claim([row(k,value=0 if k=='successful_outputs' else 'recorded') for k in REQUIREMENTS['energy_per_success']],'energy_per_success',SCOPE)
        self.assertEqual(result['missing'],[])  # Ratio remains undefined at zero.
    def test_truncated_compact_protocol(self):
        with self.assertRaises(ValueError):CompactReader(bytes([0x18,0x7f])).structure()
    def test_corrupt_parquet_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.parquet';p.write_bytes(b'PAR1'+b'\xff'*4+b'PAR1')
            with self.assertRaises(ValueError):inspect(p)

if __name__=='__main__':unittest.main()
