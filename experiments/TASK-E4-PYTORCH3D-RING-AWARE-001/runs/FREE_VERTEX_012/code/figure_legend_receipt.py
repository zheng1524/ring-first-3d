"""Display label correction only; preserve frozen numeric evaluator and original figure."""
from figures_gt import *
import inspect,shutil
p=R/'figures/Fig5_Quantitative_Results.png';archive=R/'figures/full/Fig5_Original_Legend.png'
if p.exists()and not archive.exists():shutil.copy2(p,archive)
source=inspect.getsource(metrics_figure).replace("label='occupancy proxy (inferred base)'","label='occupancy sampling estimate / proxy'").replace("'Pred H95 mm'","'Pred H95 body mm'")
exec(compile(source,__file__+':display-only','exec'),globals());metrics_figure()
save('assets_index/FIGURE_LEGEND_RECEIPT.json',dict(display_only=True,numeric_evaluator_unchanged=True,reason='G01 strict-solid IoU and raw occupancy estimate are the same estimate; not all gray bars represent inferred-base-only cases.',original_figure=asset(archive),no_prediction_or_metric_change=True))
