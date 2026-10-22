# Allen 2020 re-run

These scripts re-run the clustering of Allen et al. 2020 (eLife 9:e54074) to recover
each cell's cluster, which the authors did not publish. They reproduce the steps and
parameters of the authors' analysis pipeline, `R_preprocessing.R` in
[aaron-allen/VNC_scRNAseq](https://github.com/aaron-allen/VNC_scRNAseq) (Aaron M. Allen;
GPL-3.0), with Seurat 2.3.4 as in its `sessionInfo.txt`. The scripts here are written
afresh, not copied from it; the method, parameters and choices are the authors'.
See `docs/DESIGN.md` (*Allen 2020*) for how they were run and checked.
