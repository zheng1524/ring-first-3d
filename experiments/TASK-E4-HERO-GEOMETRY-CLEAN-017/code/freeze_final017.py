"""Reproduction helper: freeze provided final rule after initial diagnostic, before final subset."""
from common017 import *
def main():
    assert load(R/'metrics/CONTROL_TESTS.json')['passed']
    assert load(R/'metrics/TWO_SIDED_CONTROL_TESTS.json')['passed']
    assert (R/'config/FINAL_CLEANING_RULE.json').is_file()
    save('provenance/BEFORE_FINAL_CLEANING.json',dict(epoch=time.time(),rule=asset(R/'config/FINAL_CLEANING_RULE.json'),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],initial_outputs=asset(R/'provenance/OUTPUT_FREEZE.json'),initial_rule_preserved=asset(R/'config/PROTOCOL.json'),GT_opened=False))
if __name__=='__main__':main()
