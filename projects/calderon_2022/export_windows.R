#!/usr/bin/env Rscript
# Calderon et al. 2022: per-nucleus cluster assignments from the authors' modelled-window
# Seurat objects (portal: RNA/update/seurat_objects/pred_windows/NNv1/<a>_<b>_finished_processing.Rds),
# read with base R (Seurat not needed: the metadata is the object's meta.data slot).
#
# Writes .cache/calderon/cells.tsv.gz: window (e.g. 10_12), cell (the GEO cell name),
# cluster (seurat_clusters, the Table S1 cluster number), time (the collection window,
# e.g. hrs_08_12), NNv1_age.
#
# Usage (from the repo root):
#   Rscript projects/calderon_2022/export_windows.R
windows <- c("0_2", "2_4", "4_6", "6_8", "8_10", "10_12", "12_14", "14_16", "16_18")
dir <- ".cache/calderon/nnv1"
out <- gzfile(".cache/calderon/cells.tsv.gz", "w")
writeLines("window\tcell\tcluster\ttime\tNNv1_age", out)
for (w in windows) {
  md <- attr(readRDS(file.path(dir, paste0(w, "_finished_processing.Rds"))), "meta.data")
  writeLines(paste(w, rownames(md), as.character(md$seurat_clusters), as.character(md$time),
                   format(md$NNv1_age, digits = 6), sep = "\t"), out)
  cat(w, nrow(md), "nuclei,", length(unique(md$seurat_clusters)), "clusters\n")
  gc()
}
close(out)
