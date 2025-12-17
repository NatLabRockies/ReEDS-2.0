---
orphan: true
---

## Getting Started with Markdown in VSCode
The following are some markdown examples of what you might use when adding/editing the ReEDS documentation. The following are some additional resources: 
- General Markdown: [https://www.markdownguide.org/cheat-sheet/](https://www.markdownguide.org/cheat-sheet/)
- Math notation in markdown: [https://www.upyesp.org/posts/makrdown-vscode-math-notation/](https://www.upyesp.org/posts/makrdown-vscode-math-notation/)

### Tables
**Markdown Syntax: to insert table**
 
```
    ```{table} UPV and DUPV Resource Classes
    :name: upv-dupv-resource-classes

    |  Class  | GHI (kWh/m^2/day) | Potential UPV Capacity (GW) | Potential DUPV Capacity (GW) |
    |---------|-------------------|-----------------------------|------------------------------|
    |      1  |          3.0 - 3.5|                          167|                            14|
    |      2  |          3.5 - 4.0|                       16,870|                           184|
    |      3  |          4.0 - 4.5|                       30,238|                           434|
    |      4  |          4.5 - 5.0|                       37,438|                           511|
    |      5  |          5.0 - 5.5|                       20,372|                           222|
    |      6  |          5.5 - 6.0|                       11,868|                           116|
    |      7  |          6.0 - 6.5|                          332|                             4|

    ```
```

**Output**
```{table} UPV and DUPV Resource Classes
:name: upv-dupv-resource-classes

|  Class  | GHI (kWh/m^2/day) | Potential UPV Capacity (GW) | Potential DUPV Capacity (GW) |
|---------|-------------------|-----------------------------|------------------------------|
|      1  |          3.0 - 3.5|                          167|                            14|
|      2  |          3.5 - 4.0|                       16,870|                           184|
|      3  |          4.0 - 4.5|                       30,238|                           434|
|      4  |          4.5 - 5.0|                       37,438|                           511|
|      5  |          5.0 - 5.5|                       20,372|                           222|
|      6  |          5.5 - 6.0|                       11,868|                           116|
|      7  |          6.0 - 6.5|                          332|                             4|

```

**Markdown Syntax: to reference a table**

To have a numbered reference (ex: 'Table 1')
``` 
{numref}`upv-dupv-resource-classes` 
```

To have a non-numbered reference (ex: 'UPV and DUPV Resource Classes')

```
{ref}`upv-dupv-resource-classes`
```

### Figures
**Markdown Syntax: to insert figure**
```
    ```{figure} figs/docs/csp-resource-availability.png
    :name: example-figure
    
    CSP resource availability and solar field capacity factor for the contiguous United States 
    ```
```

**Output**
```{figure} figs/docs/csp-resource-availability.png
:name: example-figure

CSP Resource Availability 
```

**Markdown Syntax: to reference a figure**

To have a numbered reference (ex: 'Fig. 1')
``` 
{numref}`figure-csp-resource-availability` 
```

To have a non-numbered reference (ex: 'CSP Resource Availability')
```
{ref}`figure-csp-resource-availability` 
```

### Footnotes
To use footnotes in the documentation, follow this general structure.

**Adding a new footnote:**
```
[^ref68]: Older versions of the ReEDS model         
         (version 2022 and earlier) included the full         
        spatial dataset, and then subset the 
        model equations to only include 
        equations for the region of interest.

```


**Referencing a footnote:**

``` 
North Dakota.[^ref68] 
```



