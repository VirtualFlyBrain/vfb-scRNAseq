#!/usr/bin/env Rscript
# Allen et al. 2020 re-run, last step: assemble the aligned CCA dimensions 1-45 (from
# align_chunk.R) into the CCA-checkpoint object as the "cca.aligned" reduction and cluster
# as the authors did (Louvain on 45 aligned dimensions, resolution 12). Writes
# /data/rerun/clusters.tsv.gz (cell, cluster, sex, replicate, nGene, nUMI).
# Method and parameters: Allen et al. 2020, aaron-allen/VNC_scRNAseq (Aaron M. Allen, GPL-3.0);
# see README.md here.

library(Seurat)
out <- "/data/rerun"
VNC.combined <- readRDS(file.path(out, "after_cca.rds"))
chunks <- list.files(out, pattern = "^aligned_[0-9]+_[0-9]+\\.rds$", full.names = TRUE)
emb <- do.call(cbind, lapply(chunks, readRDS))
emb <- emb[colnames(VNC.combined@data), order(as.integer(sub("ACC", "", colnames(emb))))]
stopifnot(identical(colnames(emb), paste0("ACC", 1:45)))
VNC.combined <- SetDimReduction(VNC.combined, reduction.type = "cca.aligned", slot = "cell.embeddings", new.data = emb)
VNC.combined <- SetDimReduction(VNC.combined, reduction.type = "cca.aligned", slot = "key", new.data = "ACC")
VNC.combined <- FindClusters(VNC.combined, reduction.type = "cca.aligned", resolution = 12,
                             dims.use = 1:45, save.SNN = TRUE)
md <- VNC.combined@meta.data
cells <- names(VNC.combined@ident)
res <- data.frame(cell = cells, cluster = as.character(VNC.combined@ident), sex = md[cells, "Sex"],
                  replicate = md[cells, "Replicate"], nGene = md[cells, "nGene"], nUMI = md[cells, "nUMI"])
con <- gzfile(file.path(out, "clusters.tsv.gz"), "w")
write.table(res, con, sep = "\t", quote = FALSE, row.names = FALSE)
close(con)
cat(sprintf("%d clusters, %d cells\n", length(unique(res$cluster)), nrow(res)))
print(sort(table(res$cluster), decreasing = TRUE))
