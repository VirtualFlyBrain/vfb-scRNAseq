#!/usr/bin/env Rscript
# Allen et al. 2020 re-run, alignment step in chunks. Seurat 2.3.4's AlignSubspace aligns
# each CCA dimension independently (dynamic time warping of that dimension's metagenes
# between the two sexes), but memory is not released between dimensions, so aligning
# many dimensions in one R session runs out of memory (~3 GB per dimension here). Each
# chunk of dimensions is aligned in a fresh session from the CCA checkpoint written by
# rerun_clusters.R, with the authors' parameters; cluster_aligned.R assembles the chunks.
# Only dimensions 1-45 are needed: the authors cluster on 45 aligned dimensions (the
# alignment of a dimension does not depend on the others).
#
# Usage (in the vfbseq/seurat:2.3.4 image, .cache/allen at /data):
#   Rscript /work/align_chunk.R <first dim> <last dim>
# Writes /data/rerun/aligned_<first>_<last>.rds (cells x dims, aligned embeddings).
# Method and parameters: Allen et al. 2020, aaron-allen/VNC_scRNAseq (Aaron M. Allen, GPL-3.0);
# see README.md here.

library(Seurat)
args <- as.integer(commandArgs(trailingOnly = TRUE))
dims <- args[1]:args[2]
out <- "/data/rerun"
f <- file.path(out, sprintf("aligned_%d_%d.rds", args[1], args[2]))
if (file.exists(f)) quit(save = "no")
t0 <- Sys.time()
VNC.combined <- readRDS(file.path(out, "after_cca.rds"))
# AlignSubspace indexes its output by dimension number but builds it from the dimensions
# aligned only, so a chunk not starting at 1 fails. Each dimension is aligned on its own
# (its CCA embedding and loadings), so the chunk's dimensions are renumbered 1..k for the
# call and named back afterwards.
for (slot in c("cell.embeddings", "gene.loadings")) {
  m <- GetDimReduction(VNC.combined, reduction.type = "cca", slot = slot)[, dims, drop = FALSE]
  colnames(m) <- paste0("CC", seq_along(dims))
  VNC.combined <- SetDimReduction(VNC.combined, reduction.type = "cca", slot = slot, new.data = m)
}
VNC.combined <- AlignSubspace(VNC.combined, reduction.type = "cca", grouping.var = "Sex",
                              dims.align = seq_along(dims))
emb <- GetCellEmbeddings(VNC.combined, reduction.type = "cca.aligned")
colnames(emb) <- paste0("ACC", dims)
saveRDS(emb, f)
cat(sprintf("aligned dims %d-%d in %.1f min\n", args[1], args[2], as.numeric(difftime(Sys.time(), t0, units = "mins"))))
