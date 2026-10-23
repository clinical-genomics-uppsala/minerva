# Running the pipeline

Minerva is a [Snakemake](https://snakemake.readthedocs.io/) pipeline. All commands are run inside the [pixi](https://pixi.sh) environment defined in `pixi.toml`, either through predefined **pixi tasks** (recommended) or by calling **snakemake** directly. Do not use pip or conda directly.

## Prerequisites

1. Install pixi and the environment:

    ```bash
    pixi install
    ```

2. Prepare the input files `samples.tsv` and `units.tsv` (see [samples.tsv and units.tsv](setup.md#samplestsv-and-unitstsv)) and make sure `config/config.yaml` points to them:

    ```yaml
    samples: "config/samples.tsv"
    units: "config/units.tsv"
    ```

3. Check the main options in `config/config.yaml`, e.g. `aligner` (`vacmap` or `pbmm2`), `use_deepsomatic` (DeepSomatic-TO instead of ClairS-TO) and `reference.sv_databases`.

4. Container images are pulled automatically at runtime with Singularity/Apptainer, so it must be available on the machine that runs the pipeline.

!!! note
    Hydra-genetics modules are fetched from GitHub on the first run and kept in the Snakemake source cache. If a module has been updated on the remote and this causes problems, clear the cache.

## Pixi tasks

The tasks below are defined in `pixi.toml` and are run with `pixi run <task>`.

| Task | What it does |
|---|---|
| `pixi run all-dry` | Dry run of the full pipeline (`config/config.yaml`), 1 core |
| `pixi run all-full` | Full run, jobs submitted to SLURM with the `profiles/marvin_cpu` profile |
| `pixi run test-dry` | Dry run on the test data (`config/config.yaml` + `config/config_test.yaml`) |
| `pixi run test-full` | Full run on the test data with the `profiles/marvin_cpu` profile |
| `pixi run tests` | Unit tests |
| `pixi run precom` | Pre-commit checks |
| `pixi run fmt-wf` | Format the Snakefiles with snakefmt |

A typical workflow is to always do a dry run first and only start the real run when it succeeds:

```bash
pixi run all-dry
pixi run all-full
```

!!! warning
    `all-full` and `test-full` submit jobs to a SLURM cluster, so they should be run on the cluster login node, not on a local computer. Locally, only dry runs are meant to be used.

## Plain snakemake commands

The tasks are thin wrappers around snakemake. The equivalent commands are:

```bash
# dry run, full pipeline
pixi run snakemake --configfile config/config.yaml -n --cores 1

# dry run, test data (several config files are merged, later files override earlier ones)
pixi run snakemake --configfiles config/config.yaml config/config_test.yaml -n --cores 1

# full run on a cluster
pixi run snakemake --configfile config/config.yaml --profile profiles/marvin_cpu
```

At least one `--configfile` is required. Useful additional options:

| Option | Purpose |
|---|---|
| `-n` / `--dry-run` | Show what would be executed without running anything |
| `-p` | Print the shell commands of the jobs |
| `--cores N` | Number of local cores (required when no profile is used) |
| `--keep-going` | Continue with independent jobs if one job fails |
| `--rerun-incomplete` | Rerun jobs that were left incomplete by an interrupted run |
| `--until <rule>` | Run only up to a given rule |
| `--forcerun <rule>` | Force the rerun of a rule and everything downstream |
| `--summary` | List output files and the state of each |

See the [snakemake CLI documentation](https://snakemake.readthedocs.io/en/stable/executing/cli.html) for all options.

## Snakemake profiles

A [profile](https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles) is a `config.yaml` file in a directory that stores command line options, so that they do not have to be typed every time. It is selected with `--profile <directory>`. The pipeline ships with `profiles/marvin_cpu`, which is used by the `*-full` pixi tasks:

```yaml
jobs: 8
keep-going: True
restart-times: 2
rerun-incomplete: True
use-singularity: True
drmaa: "-p {resources.partition} -t {resources.time} -n {resources.threads} --mem={resources.mem_mb} ... -J {rule} -A wp2 -e slurm/{rule}_%j.err -o slurm/{rule}_%j.out --nodes=1-1"
drmaa-log-dir: "slurm"
singularity-args: "--cleanenv -B $HOME/.cache,/projects,/beegfs-storage,/tmp,/data/ref_genomes/VEP,/data/ref_genomes/GNOMAD"
singularity-prefix: "/path/to/singularity_cache/"
```

The most important settings are:

* `jobs` – maximum number of jobs submitted to the cluster at the same time.
* `use-singularity` and `singularity-args` – run rules in containers; `-B` binds the directories that the containers need to access (input data, reference files, VEP and gnomAD caches). Adjust these to your file system.
* `singularity-prefix` – shared location of the downloaded container images.
* `drmaa` and `drmaa-log-dir` – how jobs are submitted to SLURM (partition, account `-A`, time, memory, threads taken from each rule's resources) and where the logs are written.
* `restart-times`, `keep-going`, `rerun-incomplete` – failure handling.

The resources in `{resources.*}` come from `config/resources.yaml` (see [resources.yaml](setup.md#resourcesyaml)).

To run on another system, copy the profile and adapt the account, partition and bind paths:

```bash
cp -r profiles/marvin_cpu profiles/my_cluster
# edit profiles/my_cluster/config.yaml
pixi run snakemake --configfile config/config.yaml --profile profiles/my_cluster
```

Command line options take precedence over the profile, so e.g. `--jobs 20` overrides `jobs` in the profile.

## Output

Final results are copied to `results/` as declared in `config/output_files.yaml`, see [Result files](result_files.md). Job logs are written to `logs/` and, for cluster runs, to the directory given by `drmaa-log-dir` (`slurm/`).

## Common situations

* **Resume after a failure** – rerun the same command. Snakemake continues from the jobs that are not finished; use `--rerun-incomplete` (already set in the profile) if a run was killed.
* **Switch SNV caller** – set `use_deepsomatic: true` or `false` in `config/config.yaml` and run again.
* **Add a population SV database** – append its path to `reference.sv_databases` in `config/config.yaml`.
* **Locked directory** – after an interrupted run, unlock with `pixi run snakemake --configfile config/config.yaml --unlock`.
