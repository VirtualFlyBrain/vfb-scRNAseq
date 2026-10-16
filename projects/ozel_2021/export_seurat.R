# Export the authors' Seurat v3 objects (GSE142787_<stage>.rds) to plain files the
# pipeline reads, one folder per stage under .cache/ozel/<stage>/:
#
#   matrix.mtx.gz     raw UMI counts (RNA@counts), genes x cells, MatrixMarket
#   features.tsv.gz   gene symbol <tab> gene symbol (the objects carry symbols only)
#   barcodes.tsv.gz   cell names
#   metadata.tsv.gz   per cell: the authors' meta.data columns (library, the stage's
#                     unsupervised clusters, neural-network predictions, FinalIdents)
#
# Base R reads the objects without Seurat installed (the slots are plain attributes);
# Matrix (a recommended package) handles the dgCMatrix counts.
#
# Usage (from the repo root):  Rscript projects/ozel_2021/export_seurat.R [stage ...]
#   stages default to P15 P30 P40 P50 P70 Adult; .cache/ozel/<stage>.rds must exist.

suppressMessages(library(Matrix))
args <- commandArgs(trailingOnly = TRUE)
stages <- if (length(args)) args else c("P15", "P30", "P40", "P50", "P70", "Adult")

gz_lines <- function(lines, path) {
  con <- gzfile(path, "w"); writeLines(lines, con); close(con)
}

for (st in stages) {
  src <- file.path(".cache", "ozel", paste0(st, ".rds"))
  out <- file.path(".cache", "ozel", st)
  dir.create(out, showWarnings = FALSE, recursive = TRUE)
  t0 <- Sys.time()
  o <- suppressWarnings(readRDS(src))
  counts <- attr(attr(o, "assays")$RNA, "counts")
  md <- attr(o, "meta.data")
  stopifnot(identical(colnames(counts), rownames(md)))
  rm(o); invisible(gc())

  mtx <- file.path(out, "matrix.mtx")
  writeMM(counts, mtx)
  system2("gzip", c("-f", mtx))
  gz_lines(paste(rownames(counts), rownames(counts), sep = "\t"), file.path(out, "features.tsv.gz"))
  gz_lines(colnames(counts), file.path(out, "barcodes.tsv.gz"))
  md <- data.frame(barcode = rownames(md), md, check.names = FALSE)
  con <- gzfile(file.path(out, "metadata.tsv.gz"), "w")
  write.table(md, con, sep = "\t", quote = FALSE, row.names = FALSE)
  close(con)
  cat(sprintf("%s: %d genes x %d cells, %d non-zero; %s columns; %.0f s\n",
              st, nrow(counts), ncol(counts), length(counts@x),
              paste(colnames(md)[-1], collapse = ","), as.numeric(Sys.time() - t0, units = "secs")))
  rm(counts, md); invisible(gc())
}
