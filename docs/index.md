# Minerva

Minerva is a bioinformatic pipeline for detecting high-risk genomic markers in multiple myeloma (MM). Minerva is built using [hydra-genetics modules](https://github.com/hydra-genetics) and designed to analyse hybrid capture long-read sequencing data (PacBio HiFi) from gene panels. It uses two aligners: [VACmap](https://github.com/micahvista/VACmap) to increase sensitivity of SV-detection, and [pbmm2](https://github.com/PacificBiosciences/pbmm2) for SNVs/InDels and copy number variants (CNV).
