# Ridare -- "to give back"

A REST service to extract markdown from PASTA+ data package EML metadata and return it as HTML fragments.

Supported EML markdown fields:

```text
abstract:         dataset/abstract/markdown
description:      dataset/methods/methodStep/description/markdown
related_abstract: dataset/project/relatedProject/abstract/markdown
related_funding:  dataset/project/relatedProject/funding/markdown
```

## Examples

```shell
$ curl http://127.0.0.1:5000/markdown/abstract/edi.521.1
```
```html
<p>This SOils DAta Harmonization (SoDaH) database is designed to bring together soil carbon
data from diverse research networks into a harmonized dataset that can be used for
synthesis activities and model development. The research network sources for SoDaH span
different biomes and climates, encompass multiple ecosystem types, and have collected
data across a range of spatial, temporal, and depth gradients. The rich data sets
assembled in SoDaH consist of observations from monitoring efforts and long-term
ecological experiments. The SoDaH database also incorporates related environmental
covariate data pertaining to climate, vegetation, soil chemistry, and soil physical
properties. The data are harmonized and aggregated using open-source code that enables 
a scripted, repeatable approach for soil data synthesis.</p>
```

```shell
$ curl http://127.0.0.1:5000/markdown/related_funding/knb-lter-cap.689.1
```
```html
<ul>
<li>NSF SUCCESSION-I 1977-1979 DEB-7724478 (Fisher)</li>
<li>NSF SUCCESSION-II 1980-1983 DEB-8004145 (Fisher)</li>
<li>NSF SUCCESSION-III 1984-1987 BSR-8406891 (Fisher)</li>
<li>NSF Postdoc 1987-1989 BSR 87-00122 (Grimm)</li>
<li>NSF STABILITY - 1989-1992 BSR-8818612 (Fisher and Grimm)</li>
<li>NSF TROPHIC STRUCTURE 1990-1992 BSR-9008114 (Fisher, Grimm, and Dudley)</li>
<li>NSF LTREB I - 1991-1996 DEB-9108362 (Grimm and Fisher)</li>
<li>NSF HETEROGENEITY - 1993-1998 DEB-9306909 (Fisher and Grimm)</li>
<li>EPA HYPORHEIC - 1994-1996 #R821250-01-0 (Fisher and Grimm)</li>
<li>NSF LINX I - 1996-1999 - DEB-9628860 (subaward to Grimm, Marti, and Fisher)</li>
<li>NSF LTREB II - 1996-2001 DEB-9615358 (Grimm and Fisher)</li>
<li>NSF LINX II - 2001-2006 DEB-0111410 (subaward to Grimm and Dahm)</li>
<li>NSF LTREB III - 2009-2015 DEB-0918262 (Grimm and Sabo)</li>
<li>NSF LTREB IV - 2015-2020 DEB-1457227 (Grimm and Sabo)</li>
<li>NSF LINKAGES - 1998-2000 DEB-9727311 (Fisher and Grimm)</li>
<li>NSF DDIG - 1998-1999 DEB-9800912 (Dent and Grimm)</li>
</ul> 
```
## Notes

[Overview of markdown support in EML](https://eml.ecoinformatics.org/whats-new-in-eml-2-2-0.html)
