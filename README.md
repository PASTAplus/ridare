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

## Install

- Clone from GitHub
- Download DocBook XSLs and uncompress into the root of the project
    - https://github.com/docbook/xslt10-stylesheets/releases/download/release/1.79.2/docbook-xsl-1.79.2.zip

## Troubleshooting

If Ridare returns an unexpected result, the XML fragment that was extracted from the EML
document can be returned directly without any further processing by Ridare. This is
triggered by starting the REST URL with `/raw/`.
E.g., `http://ridare.edirepository.org/raw/knb-lter-sbc.1001.7///dataset/abstract`

## Notes

[Overview of markdown support in EML 2.2.0](https://eml.ecoinformatics.org/whats-new-in-eml-2-2-0.html)
