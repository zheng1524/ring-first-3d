"""Apply all preregistered reference identities; no metric or optimization rerun."""
from correction import *
def main():
    old=R/'config/ORIGINAL_QUALIFICATION.json';preserved=R/'runtime/ORIGINAL_QUALIFICATION_INITIAL001.json'
    assert not preserved.exists();preserved.write_bytes(old.read_bytes())
    original=load(R/'config/ORIGINAL_TEST12.json');obs=load(R/'config/ORIGINAL_OBSERVABILITY.json');before=load(old)
    after={c:dict(original_status=original_status(c,original,obs[c])[0],reasons=original_status(c,original,obs[c])[1]) for c in IDS}
    save('config/ORIGINAL_QUALIFICATION.json',after)
    save('config/ADJUDICATION_IMPLEMENTATION_FIX.json',dict(reason='ENG02 preliminary reducer counted two relations but omitted the frozen required ref13 identity for new candidates; require every frozen baseline identity. Thresholds, RGB-only selection, data and optimization unchanged.',user_requirement='ref03/ref08 for fitting, ref13 extra held-out check',before=before,after=after,preserved_local_artifact=asset(preserved),metrics_unchanged=asset(R/'config/ORIGINAL_TEST12.json'),correction_not_rerun=True,optimizer_calls=sum(r['optimizer_calls'] for r in load(R/'config/BOUNDED_CORRECTION_RESULTS.json'))))
    print('ADJUDICATION_FIXED_REQUIRED_REF13',[(short(c),r['original_status']) for c,r in after.items()],flush=True)
if __name__=='__main__':main()
