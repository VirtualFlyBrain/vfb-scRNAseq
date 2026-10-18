# Seurat 2.3.4 on R 3.5.3, as in the authors' sessionInfo.txt (aaron-allen/VNC_scRNAseq),
# with CRAN packages from a snapshot taken before Seurat 3.0 was released (2019-04-16).
FROM rocker/r-ver:3.5.3
RUN sed -i 's|deb.debian.org|archive.debian.org|g; s|security.debian.org|archive.debian.org|g; /stretch-updates/d' /etc/apt/sources.list \
 && apt-get -o Acquire::Check-Valid-Until=false update \
 && apt-get install -y --no-install-recommends libhdf5-dev libcurl4-openssl-dev libssl-dev libxml2-dev \
      libpng-dev zlib1g-dev libgsl-dev libglpk-dev libgmp-dev \
 && rm -rf /var/lib/apt/lists/*
RUN echo 'options(repos = c(CRAN = "https://packagemanager.posit.co/cran/2019-04-10"), Ncpus = 6)' >> /usr/local/lib/R/etc/Rprofile.site \
 && Rscript -e 'install.packages(c("Seurat", "dplyr", "future"))' \
 && Rscript -e 'stopifnot(packageVersion("Seurat") == "2.3.4"); cat("Seurat", as.character(packageVersion("Seurat")), "\n")'
