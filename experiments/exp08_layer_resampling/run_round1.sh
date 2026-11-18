#!/usr/bin/env bash
# Round 1 launcher: builds the bin-averaged tensors on CPU while each GPU runs
# its interp cell, then each GPU runs its binavg cell. Run from the repo root:
#   nohup bash experiments/exp08_layer_resampling/run_round1.sh > outputs/logs/exp08_launcher.log 2>&1 &
set -u
P=/home/ap9107/anaconda3/envs/truckidme/bin/python
M=experiments.exp08_layer_resampling
L=outputs/logs

for w in 30 51.2 90 120; do
  $P -u -m $M.build_binavg_tensors --window $w > $L/exp08_binavg_$w.log 2>&1 &
done
BUILD_PIDS=$(jobs -p)

gpu_chain () {   # $1 = gpu index, $2 = layer
  CUDA_VISIBLE_DEVICES=$1 $P -u -m $M.round1 --layer $2 --resampling interp
  wait $BUILD_PIDS 2>/dev/null
  CUDA_VISIBLE_DEVICES=$1 $P -u -m $M.round1 --layer $2 --resampling binavg
}
gpu_chain 0 2  > $L/exp08_gpu0_layer2.log 2>&1 &
gpu_chain 1 -1 > $L/exp08_gpu1_final.log 2>&1 &
wait
$P -m $M.summarise > $L/exp08_summary.log 2>&1
echo "ROUND 1 COMPLETE"
