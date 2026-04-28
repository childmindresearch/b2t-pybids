# b2t-pybids

This project analyzes pybids usage patterns across neuroimaging pipelines to develop an expanded API wrapper around bids2table (b2t).

## Goal

Expand the bids2table API to capture common usage patterns of pybids used in various pipelines and libraries, enabling the retirement of the over-engineered pybids package.

## Submodules

### Core Libraries

- **pybids**: The library being replaced
- **bids2table**: The target library to wrap

### Projects (pybids users)

This repository contains several major pybids-using projects as submodules for analysis:

- **fmriprep**: fMRI preprocessing pipeline
- **smriprep**: Structural MRI preprocessing pipeline
- **nibabies**: Infant fMRI preprocessing pipeline
- **mriqc**: MRI quality control pipeline
- **qsiprep**: Diffusion MRI preprocessing pipeline
- **fitlins**: fMRI analysis workflow
- **niworkflows**: Common neuroimaging workflow components
- **templateflow**: Template and atlas repository (advanced PyBIDS usage)
- **bids-apps-example**: Example BIDS application
- **neurosynth**: Meta-analysis framework (no PyBIDS usage found)

### Datasets

- **bids-examples**: Official BIDS example datasets for testing

## Usage

Clone with submodules:
```bash
git clone --recursive <repo-url>
```

Or initialize submodules after cloning:
```bash
git submodule update --init --recursive
```
