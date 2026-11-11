"""Create an empty isolated replay with frozen inputs; never copies old predictions."""
from pathlib import Path
import argparse,shutil,json
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();src=Path(__file__).resolve().parents[1];out=Path(args.output).expanduser().resolve();assert out!=src and not out.is_relative_to(src),'Use a separate replay directory';assert not out.exists()or not any(out.iterdir()),'Refuse to overwrite nonempty directory';out.mkdir(parents=True,exist_ok=True)
 for folder in ['code','config']:shutil.copytree(src/folder,out/folder)
 for folder in ['inputs','features','landmarks','matches','ring','ring_evidence_v2']:(out/folder).symlink_to((src/folder).resolve(),target_is_directory=True)
 for folder in ['observations','provenance','metrics','runtime','results','optimization','figures','derived','evaluation','assets_index']:(out/folder).mkdir(exist_ok=True)
 (out/'REPLAY_SOURCE.json').write_text(json.dumps(dict(source=str(src),code_source_only=True,no_predictions_or_checkpoints_copied=True,readonly_input_links=True,run='prepare021,identity021,assets021,gate021,tolerance_check021,ba021 then postprocessors',raw_assets='Absolute paths and SHA in original config; restore exact files if missing, never substitute'),indent=2)+'\n');print('CREATED_ISOLATED_REPLAY',out)
if __name__=='__main__':main()
