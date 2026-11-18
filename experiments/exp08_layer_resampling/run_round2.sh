#!/usr/bin/env bash
# Round 2 launcher: 8 cells (4 windows x 2 resamplings), 5 partitions each,
# split across both GPUs (~3.2 h each). Run from the repo root:
#   nohup bash experiments/exp08_layer_resampling/run_round2.sh > outputs/logs/exp08_round2_launcher.log 2>&1 &
set -u
P=/home/ap9107/anaconda3/envs/truckidme/bin/python
M=experiments.exp08_layer_resampling.round2
L=outputs/logs

chain () {   # $1 = gpu, rest = window:resampling pairs
  gpu=$1; shift
  for job in "$@"; do
    w=${job%%:*}; r=${job##*:}
    echo "[gpu$gpu] start $r $w s  $(date +%H:%M)"
    CUDA_VISIBLE_DEVICES=$gpu $P -u -m $M --window $w --resampling $r
    echo "[gpu$gpu] done  $r $w s  $(date +%H:%M)"
  done
}
chain 0 30:interp 30:binavg 90:interp 120:interp     > $L/exp08_r2_gpu0.log 2>&1 &
chain 1 51.2:interp 51.2:binavg 90:binavg 120:binavg > $L/exp08_r2_gpu1.log 2>&1 &
wait
$P -m $M --summarise > $L/exp08_round2_summary.log 2>&1
echo "ROUND 2 COMPLETE $(date +%H:%M)"
