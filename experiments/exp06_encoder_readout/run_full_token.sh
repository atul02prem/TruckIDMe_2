#!/usr/bin/env bash
# Fine-tuned token comparison: cls_token on GPU0, combined on GPU1 (~2 h each).
# Run from the repo root:
#   nohup bash experiments/exp06_encoder_readout/run_full_token.sh > outputs/logs/exp06_full_token_launcher.log 2>&1 &
P=/home/ap9107/anaconda3/envs/truckidme/bin/python
M=experiments.exp06_encoder_readout.full_token
CUDA_VISIBLE_DEVICES=0 $P -u -m $M --token cls_token > outputs/logs/exp06_full_cls.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 $P -u -m $M --token combined  > outputs/logs/exp06_full_combined.log 2>&1 &
wait
$P -u -m $M --summarise
echo "FULL TOKEN COMPLETE $(date +%H:%M)"
