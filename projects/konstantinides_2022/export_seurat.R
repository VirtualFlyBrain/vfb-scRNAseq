# Export the authors' Seurat object (GSE167266 OL.L3_P15_merged.rds) to plain files the
# pipeline reads, under .cache/konstantinides/:
#
#   metadata.tsv.gz      per cell, all cells: the authors' meta.data columns (library
#                        `orig.ident`: Lib1-Lib10 for L3, 1-3 for the Özel P15 cells;
#                        the L3 clusters `integrated_snn_res.2`; `Neuropil`; ...)
#   L3/matrix.mtx.gz     raw UMI counts (RNA@counts) of the L3 cells, genes x cells
#   L3/features.tsv.gz   gene symbol <tab> gene symbol (the object carries symbols only)
#   L3/barcodes.tsv.gz   cell names
#
# The P15 cells are Özel 2021's (ozel_2021), not part of the L3 clustering, so only the
# L3 counts are exported. Base R reads the object without Seurat installed (the slots
# are plain attributes); Matrix (a recommended package) handles the dgCMatrix counts.
#
# Usage (from the repo root):  Rscript projects/konstantinides_2022/export_seurat.R
#   .cache/konstantinides/OL.L3_P15_merged.rds must exist.

suppressMessages(library(Matrix))

gz_lines <- function(lines, path) {
  con <- gzfile(path, "w"); writeLines(lines, con); close(con)
}

base <- file.path(".cache", "konstantinides")
out <- file.path(base, "L3")
dir.create(out, showWarnings = FALSE, recursive = TRUE)
t0 <- Sys.time()
o <- suppressWarnings(readRDS(file.path(base, "OL.L3_P15_merged.rds")))
counts <- attr(attr(o, "assays")$RNA, "counts")
md <- attr(o, "meta.data")
stopifnot(identical(colnames(counts), rownames(md)))
rm(o); invisible(gc())

mdo <- data.frame(barcode = rownames(md), md, check.names = FALSE)
con <- gzfile(file.path(base, "metadata.tsv.gz"), "w")
write.table(mdo, con, sep = "\t", quote = FALSE, row.names = FALSE)
close(con)

l3 <- grepl("^Lib", as.character(md$orig.ident))
counts <- counts[, l3]
mtx <- file.path(out, "matrix.mtx")
writeMM(counts, mtx)
system2("gzip", c("-f", mtx))
gz_lines(paste(rownames(counts), rownames(counts), sep = "\t"), file.path(out, "features.tsv.gz"))
gz_lines(colnames(counts), file.path(out, "barcodes.tsv.gz"))
cat(sprintf("L3: %d genes x %d cells, %d non-zero (of %d cells in the object); %.0f s\n",
            nrow(counts), ncol(counts), length(counts@x), nrow(md),
            as.numeric(Sys.time() - t0, units = "secs")))
