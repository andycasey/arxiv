Impact of the COVID-19 pandemic on academic productivity
========================================================

Here we describe how those data were collected. 
We downloaded the [arXiv dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) hosted by Kaggle on 2022 June 6. 
This dataset is a JSON file (named `arxiv-metadata-oai-snapshot.json`) compressed into a zip file.

We then executed the `process.py` file to create three files: 
- `metadata.json`: titles, abstract, and affiliations of authors
- `authors.json`: author names
- `records.csv`: arXiv identifier, categories, number of authors and affiliations, abstract length

We excluded pre-prints from 2022 June when processing files. The `process.py` script also adds a 'dummy' line to the `records.csv` to make Python load arXiv identifiers as strings. These three files (`metadata.json`, `authors.json`, and `records.csv`) were used for this analysis.
