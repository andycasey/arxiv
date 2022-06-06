

Software environment
--------------------

To reproduce this work you will need to create a Conda environment that has the requisite Python packages.

First, make sure you have Conda installed. Then clone this repository and create the environment:
```
git clone git@github.com:andycasey/arxiv.git
cd arxiv/
conda env create -f environment.yml
```

To activate the new environment:
```
conda activate covid
```

Retrieving the data
------------------

The data used in this work has been uploaded to Zenodo as . You can reproduce this work by downloading the contents of that Zenodo package and extracting it to the `data/` folder in this repository.

Here we describe how those data were collected. 
We used the (arXiv Dataset)[https://www.kaggle.com/datasets/Cornell-University/arxiv] hosted by Kaggle, which contains metadata of over 1.7M scholarly papers. 
This dataset is a JSON file (named `arxiv-metadata-oai-snapshot.json`) compressed into a zip file.
Decompress this file and store it in the `data` directory as `data/arxiv-metadata-oai-snapshot.json`.
Each row describes an arXiv preprint. 

We then executed the `data/process.py` file (in this repository) to create three files: 
- `data/metadata.json`: titles, abstract, and affiliations of authors
- `data/authors.json`: author names
- `data/records.csv`: arXiv identifier, categories, number of authors and affiliations, abstract length

The `data/process.py` script also adds a 'dummy' line to the `data/records.csv` to make Python load arXiv identifiers as strings. 
The code to load the records (`load_records` in `plot_utils.py`) ignores this dummy line, but if you write your own code then you should be aware of this.

These three files (`metadata.json`, `authors.json`, and `records.csv`) were used for this analysis, and were uploaded to Zenodo.

Reproducing this work
---------------------

The following scripts will create the figures in the paper:
- Figure 1: `plot-pre-prints-segmented-by-field.py` will create `article/pre-prints-segmented-by-field.pdf`
- Figure 2: `plot-pandemic-related-preprints.py` will create `article/pandemic-related-preprints.pdf`
- Figure 3: `plot-new-authors-segmented-by-field.py`: will create `article/new-authors-segmented-by-field-combined.pdf`

The predicted number of articles per field (Table 1 in the paper) is printed by the `plot-pre-prints-segmented-by-field.py` script, which is also used to create Figure 1.
