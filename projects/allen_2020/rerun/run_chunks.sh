#!/usr/bin/env bash
# Allen et al. 2020 re-run after the CCA checkpoint: check that renumbering a chunk does not
# change its alignment (dims 2-3 alone vs. within 1-3), align dims 1-45 in chunks of 3, each
# in a fresh R session (align_chunk.R), then cluster (cluster_aligned.R). Run from the repo
# root; log in .cache/allen/chunks.log.
set -u
log=.cache/allen/chunks.log
R() { docker run --rm --platform linux/amd64 -v "$PWD/.cache/allen:/data" \
        -v "$PWD/projects/allen_2020/rerun:/work" vfbseq/seurat:2.3.4 "$@"; }
: >> "$log"
R Rscript /work/align_chunk.R 1 3 2>&1 | grep -E -i "aligned dims|error|halted" >> "$log"
R Rscript /work/align_chunk.R 2 3 2>&1 | grep -E -i "aligned dims|error|halted" >> "$log"
R Rscript -e 'a <- readRDS("/data/rerun/aligned_1_3.rds"); b <- readRDS("/data/rerun/aligned_2_3.rds"); cat(sprintf("validation: max abs difference dims 2-3 = %g\n", max(abs(a[rownames(b), c("ACC2", "ACC3")] - b))))' >> "$log" 2>&1
rm -f .cache/allen/rerun/aligned_2_3.rds
for a in $(seq 4 3 43); do
  R Rscript /work/align_chunk.R "$a" $((a + 2)) 2>&1 | grep -E -i "aligned dims|error|halted" >> "$log"
done
R Rscript /work/cluster_aligned.R >> "$log" 2>&1
echo "cluster exit $?" >> "$log"
