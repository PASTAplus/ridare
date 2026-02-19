# Ridare -- "to give back"

A REST service to extract markdown from PASTA+ data package EML metadata and return it
as HTML fragments.

## API

This service takes a PASTA DataPackage identifier and the Xpath to a TextType element in
the EML metadata for the package, and returns an HTML fragment containing the contents
of the element.

The TextType element may contain plain text, DocBook XML, Markdown, or a mix of those,
as described in the documentation for the EML metadata language.

By default, the service looks for DataPackages in the PASTA+ production environment.
Data packages can also be read from the development or staging environments.

| Function      | URL                               |
|---------------|-----------------------------------|
| Fetch HTML    | /<package identifier>/<xpath>     |
| Fetch raw XML | /raw/<package identifier>/<xpath> |

Valid query parameters:

| Parameter | Values                 |
|-----------|------------------------|
| env       | p, prod, or production |
|           | d, dev, or development |
|           | s, stage, or staging   |

Xpaths to commonly used EML TextType elements:

| TextType Element                                                 | Xpath                                     |
|------------------------------------------------------------------|-------------------------------------------|
| Abstract                                                         | //dataset/abstract                        |
| Description of a step of a procedure used for creating a dataset | //dataset/methods/methodStep/description  |
| Abstract for a project related to a dataset                      | //dataset/project/relatedProject/abstract | 
| Funding source for a project related to a dataset                | //dataset/project/relatedProject/funding  |

### Examples

Retrieve the `//dataset/abstract` for the `edi.521.1` DataPackage, in the `production`
environment:

```shell
$ curl https://ridare.edirepository.org/edi.521.1/%2F%2Fdataset%2Fabstract
```

Retrieve the `//dataset/abstract` for the `edi.521.1` DataPackage, in the `development`
environment:

```shell
$ curl https://ridare.edirepository.org/edi.521.1/%2F%2Fdataset%2Fabstract?env=d
```

Retrieve the `funding for related document` (
Xpath `//dataset/project/relatedProject/funding/`) for the `knb-lter-cap.689.1`
DataPackage, in the `development` environment:

```shell
$ curl https://ridare.edirepository.org/\
knb-lter-cap.689.1/%2F%2Fdataset%2Fproject%2FrelatedProject%2Ffunding?env=d
```

On success, a HTML fragment is returned with HTTP response status code `200`. E.g.:

```html
<div>
  <div>
    <p>The Santa Barbara Channel MBON tracks long-term patterns in species
      abundance and diversity.
    </p>
  </div>
  <div>
    <p>The four contributing projects are two research projects: the Santa Barbara
      Coastal LTER (SBC LTER) and the Partnership for Interdisciplinary Studies of
      Coastal Oceans (PISCO), and the kelp forest monitoring program of the Santa
      Barbara Channel National Park, and the San Nicolas Island monitoring program
      supported by USGS.
    </p>
  </div>
</div>
```

### Errors

On failure, a HTTP response with status of 4xx or 500x is returned as follows:

- PASTA returns 5xx
    - Ridare returns 500
        - body: PASTA Internal Server Error
- PASTA returns 404
    - Ridare returns 400
        - body: DataPackage not found
- PASTA returns 4xx other than 404
    - Ridare returns 400
        - body: Copy of body returned from PASTA
- Xpath does not reference an existing element
    - Ridare returns 200
        - body: Xpath not found: \<xpath\>
- Other errors, e.g., invalid URL (404) or internal error (5xx)
    - Returned directly

The HTTP document body may contain more information about the nature of the failure.

## Multi endpoint (/multi)

The /multi endpoint runs one or more XPath queries against one or more EML documents (by PID) and returns an XML resultset containing one `<document>` element per PID.

- Method: POST  
- URL: /multi  
- Content-Type: application/json  
- Response Content-Type: application/xml

Request parameters  
- JSON body:  
  - pid: list of data package IDs (PIDs) - required  
  - query: list of XPath queries - required  
    - Each item can be either:  
      - a string: an XPath expression whose results are appended directly into the document, or  
      - a single-key object: { "tagName": "xpath" } - results for the xpath are wrapped under `<tagName>...</tagName>` before being appended.  
- Optional query string:  
  - env: one of the configured PASTA environments (e.g. `development`, `staging`, `production`). Defaults to `production` environment.

### Examples

Simple single-PID, single-XPath: 
```json
{
  "pid": ["edi.521.1"],  
  "query": ["dataset/title"]  
}
```

Multiple PIDs and a labeled query:  
```json
{
  "pid": ["edi.521.1", "knb-lter-sbc.1001.7"],  
  "query": [
    "dataset/title",  
    { "projectTitle": "dataset/project/title" }  
  ]  
}
```

Example curl:
```bash
curl -X POST "https://ridare.edirepository.org/multi" \
  -H "Content-Type: application/json" \
  -d '{"pid":["edi.521.1", "knb-lter-sbc.1001.7"],"query":["dataset/title", {"projectTitle":"dataset/project/title"}]}'
```

Example response (abridged):
```xml
<?xml version="1.0" encoding="utf-8"?>  
<resultset>  
  <document>  
    <packageid>edi.521.1</packageid>  
    <title>Example dataset title</title>  
    <projectTitle>  
      <title>Project title here</title>  
    </projectTitle>  
  </document>  
  <document>  
    <packageid>knb-lter-sbc.1001.7</packageid>  
    ...  
  </document>  
</resultset>
```

### Errors

Error cases and status codes:  
- 200: OK - returned with `application/xml` and the XML resultset.  
- 400: Bad request - returned for:  
  - invalid JSON or non-JSON body ("Invalid request format"),  
  - missing/invalid `pid` or `query` fields,  
  - empty PID list or PID containing an empty string ("Data package error"),  
  - invalid `env` parameter mapping to a PastaEnvironmentError ("PASTA environment error").


## Install

- Clone from GitHub
- Download DocBook XSLs and uncompress into the root of the project
    - https://github.com/docbook/xslt10-stylesheets/releases/download/release/1.79.2/docbook-xsl-1.79.2.zip


## Conda Environment

### Server: Procedure for updating the Conda environment and all dependencies

```shell
conda deactivate
conda update -n base -c defaults conda
conda update --all
conda env remove --yes --name ridare
conda env create --file environment-min.yml
conda activate ridare
```

### Dev: Procedure for updating the Conda environment and all dependencies

Full "Server" procedure, plus update the `environment.yml` and `requirements.txt` files:

```shell
conda env export --no-builds > environment.yml
pip list --format freeze > requirements.txt
```

### If Conda base won't update to latest version, try:

```shell
conda install conda==<version>
``` 

## Quick sanity check after updates

Open a package which uses Markdown in the abstract, e.g. `knb-lter-cap.704.1` in the landing page on portal-d:

https://portal-d.edirepository.org/nis/mapbrowse?scope=knb-lter-cap&identifier=704

Then remove the cached entry in Ridare production for that package:

```shell
rm /home/pasta/ridare/cache/dev/__dataset_abstract-knb_lter_cap_704_1.html
```

Then refresh the package in the landing page and verify that the abstract is rendered correctly, and that the cached entry is recreated in Ridare:

```shell
ll /home/pasta/ridare/cache/dev/__dataset_abstract-knb_lter_cap_704_1.html
```

## Troubleshooting

If Ridare returns an unexpected result, the XML fragment that was extracted from the EML
document can be returned directly without any further processing by Ridare. This is
triggered by starting the REST URL with `/raw/`.
E.g., `http://ridare.edirepository.org/raw/knb-lter-sbc.1001.7///dataset/abstract`

## Notes

[Overview of markdown support in EML 2.2.0](https://eml.ecoinformatics.org/whats-new-in-eml-2-2-0.html)
