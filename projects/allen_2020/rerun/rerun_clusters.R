#!/usr/bin/env Rscript
# Allen et al. 2020: re-run the authors' clustering (R_preprocessing.R in
# aaron-allen/VNC_scRNAseq, Seurat 2.3.4) on the GEO matrices, to recover each cell's
# cluster, which was not published. The steps and parameters are the authors' (filtering,
# per-sex merge / normalise / scale with regression, variable genes, CCA on 100 CCs,
# AlignSubspace, Louvain on 45 aligned CCs at resolution 12); only the input paths and
# the core count differ, and the t-SNE (which does not affect the clusters) is skipped.
# The result is checked against the cluster sizes in the paper's Figure 1-source data 2.
#
# Run in the vfbseq/seurat:2.3.4 image (Dockerfile here), with .cache/allen mounted at /data:
#   docker run --rm --platform linux/amd64 -v "$PWD/.cache/allen:/data" \
#     -v "$PWD/projects/allen_2020/rerun:/work" vfbseq/seurat:2.3.4 Rscript /work/rerun_clusters.R
# Writes /data/rerun/clusters.tsv.gz (cell, cluster, sex, replicate, nGene, nUMI).

library(Seurat)
library(dplyr)
library(future)
cores <- 6
plan("multiprocess", workers = cores)

NumberOfCCAs <- 45
nGeneLowCutOff <- 200
nGeneHighCutOff <- Inf
nUMILowCutOff <- 1200
nUMIHighCutOff <- 10000
ClusterResolution <- 12
MitoLowCutOff <- -Inf
MitoHighCutOff <- 0.15

out <- "/data/rerun"
dir.create(out, showWarnings = FALSE)
t0 <- Sys.time()
step <- function(msg) cat(sprintf("[%s] %s\n", format(round(difftime(Sys.time(), t0, units = "mins"), 1)), msg))

cca_file <- file.path(out, "after_cca.rds")
if (!file.exists(cca_file)) {
  # Load Data (GEO GSE141807: the authors' top-30,000-cell DGE matrices)
  read_dge <- function(f) Matrix(as.matrix(read.table(file.path("/data/InputFiles", f), header = TRUE, sep = "\t", row.names = 1)), sparse = TRUE)
  MaleVNCRep1.data <- read_dge("GSM4213598_male_rep1_dge.txt.gz")
  FemaleVNCRep1.data <- read_dge("GSM4213596_female_rep1_dge.txt.gz")
  MaleVNCRep2.data <- read_dge("GSM4213599_male_rep2_dge.txt.gz")
  FemaleVNCRep2.data <- read_dge("GSM4213597_female_rep2_dge.txt.gz")
  step("loaded")

  MaleVNCRep1 <- CreateSeuratObject(raw.data = MaleVNCRep1.data, min.cells = 3, min.genes = nGeneLowCutOff, project = "vnc")
  FemaleVNCRep1 <- CreateSeuratObject(raw.data = FemaleVNCRep1.data, min.cells = 3, min.genes = nGeneLowCutOff, project = "vnc")
  MaleVNCRep2 <- CreateSeuratObject(raw.data = MaleVNCRep2.data, min.cells = 3, min.genes = nGeneLowCutOff, project = "vnc")
  FemaleVNCRep2 <- CreateSeuratObject(raw.data = FemaleVNCRep2.data, min.cells = 3, min.genes = nGeneLowCutOff, project = "vnc")

  MaleVNCRep1@meta.data$Replicate <- "rep3"
  MaleVNCRep2@meta.data$Replicate <- "rep4"
  FemaleVNCRep1@meta.data$Replicate <- "rep1"
  FemaleVNCRep2@meta.data$Replicate <- "rep2"

  add_mito <- function(o) {
    mito.genes <- grep(pattern = "^mt:", x = rownames(x = o@data), value = TRUE)
    prop.mito <- Matrix::colSums(o@raw.data[mito.genes, ]) / Matrix::colSums(o@raw.data)
    AddMetaData(object = o, metadata = prop.mito, col.name = "prop.mito")
  }
  MaleVNCRep1 <- add_mito(MaleVNCRep1)
  MaleVNCRep2 <- add_mito(MaleVNCRep2)
  FemaleVNCRep1 <- add_mito(FemaleVNCRep1)
  FemaleVNCRep2 <- add_mito(FemaleVNCRep2)

  MaleVNC.combined <- MergeSeurat(object1 = MaleVNCRep1, object2 = MaleVNCRep2, do.normalize = FALSE,
                                  add.cell.id1 = "rep1", add.cell.id2 = "rep2", project = "vnc")
  FemaleVNC.combined <- MergeSeurat(object1 = FemaleVNCRep1, object2 = FemaleVNCRep2, do.normalize = FALSE,
                                    add.cell.id1 = "rep1", add.cell.id2 = "rep2", project = "vnc")
  MaleVNC.combined@meta.data$Sex <- "male"
  FemaleVNC.combined@meta.data$Sex <- "female"
  rm(MaleVNCRep1.data, FemaleVNCRep1.data, MaleVNCRep2.data, FemaleVNCRep2.data,
     MaleVNCRep1, FemaleVNCRep1, MaleVNCRep2, FemaleVNCRep2)
  invisible(gc())

  # filter, normalize, and scale data
  MaleVNC.combined <- FilterCells(object = MaleVNC.combined, subset.names = c("nGene", "nUMI", "prop.mito"),
                                  low.thresholds = c(nGeneLowCutOff, nUMILowCutOff, MitoLowCutOff),
                                  high.thresholds = c(nGeneHighCutOff, nUMIHighCutOff, MitoHighCutOff))
  MaleVNC.combined <- NormalizeData(MaleVNC.combined)
  MaleVNC.combined <- ScaleData(object = MaleVNC.combined, vars.to.regress = c("Replicate", "nUMI", "prop.mito"),
                                do.par = TRUE, num.cores = cores)
  FemaleVNC.combined <- FilterCells(object = FemaleVNC.combined, subset.names = c("nGene", "nUMI", "prop.mito"),
                                    low.thresholds = c(nGeneLowCutOff, nUMILowCutOff, MitoLowCutOff),
                                    high.thresholds = c(nGeneHighCutOff, nUMIHighCutOff, MitoHighCutOff))
  FemaleVNC.combined <- NormalizeData(FemaleVNC.combined)
  FemaleVNC.combined <- ScaleData(object = FemaleVNC.combined, vars.to.regress = c("Replicate", "nUMI", "prop.mito"),
                                  do.par = TRUE, num.cores = cores)
  step(sprintf("filtered and scaled: %d male, %d female cells", ncol(MaleVNC.combined@data), ncol(FemaleVNC.combined@data)))

  # use variable genes
  MaleVNC.combined <- FindVariableGenes(MaleVNC.combined, x.low.cutoff = 0.001, x.high.cutoff = Inf, y.cutoff = 0.001,
                                        do.plot = FALSE)
  FemaleVNC.combined <- FindVariableGenes(FemaleVNC.combined, x.low.cutoff = 0.001, x.high.cutoff = Inf, y.cutoff = 0.001,
                                          do.plot = FALSE)
  genes.use <- unique(c(MaleVNC.combined@var.genes, FemaleVNC.combined@var.genes))
  genes.use <- intersect(genes.use, rownames(MaleVNC.combined@scale.data))
  genes.use <- intersect(genes.use, rownames(FemaleVNC.combined@scale.data))
  step(sprintf("%d genes for CCA", length(genes.use)))

  VNC.combined <- RunCCA(MaleVNC.combined, FemaleVNC.combined, genes.use = genes.use, num.cc = 100,
                         add.cell.id1 = "Male", add.cell.id2 = "Female")
  saveRDS(VNC.combined, cca_file)
  step("CCA (checkpoint written; re-run to align)")
  quit(save = "no")
}
# Alignment from the CCA checkpoint, in a fresh R session: AlignSubspace runs serially
# (its parallel workers each copy the data and ran out of memory in ~27 GB; the worker
# count does not change the result).
VNC.combined <- readRDS(cca_file)
step("CCA (from checkpoint)")
VNC.combined <- AlignSubspace(VNC.combined, reduction.type = "cca", grouping.var = "Sex", dims.align = 1:100,
                              do.par = FALSE)
step("aligned")
VNC.combined <- FindClusters(VNC.combined, reduction.type = "cca.aligned", resolution = ClusterResolution,
                             dims.use = 1:NumberOfCCAs, save.SNN = TRUE)
step(sprintf("%d clusters, %d cells", length(levels(VNC.combined@ident)), length(VNC.combined@ident)))

md <- VNC.combined@meta.data
res <- data.frame(cell = names(VNC.combined@ident), cluster = as.character(VNC.combined@ident),
                  sex = md[names(VNC.combined@ident), "Sex"], replicate = md[names(VNC.combined@ident), "Replicate"],
                  nGene = md[names(VNC.combined@ident), "nGene"], nUMI = md[names(VNC.combined@ident), "nUMI"])
con <- gzfile(file.path(out, "clusters.tsv.gz"), "w")
write.table(res, con, sep = "\t", quote = FALSE, row.names = FALSE)
close(con)
saveRDS(VNC.combined, file.path(out, "VNC.combined.rds"))
print(sort(table(res$cluster), decreasing = TRUE))
step("done")
