# bcs_thesis

Repository for my **Bachelor of Computer Science** experimental thesis. Written under *Prof.* Giacomo Fiumara's supervision for [**Università degli Studi di Messina**](https://unime.it).

The thesis is divided in three parts:

1. Analysis of entity encoding and **Entity-Component-System** architectural patterns. 

2. Design and implementation of [**ECST**](https://github.com/SuperV1234/ecst), a C++14 compile-time multithreaded ECS library.

3. Overview and *inner parallelism* benchmarks of a small particle simulation written using [ECST](https://github.com/SuperV1234/ecst).


## Quick shortcuts


* [**Web version PDF**](https://github.com/SuperV1234/bcs_thesis/blob/master/final/rev1/web_version.pdf) *(latest revision)*

* [Print version PDF](https://github.com/SuperV1234/bcs_thesis/blob/master/final/rev0/print_version.pdf) *(rev. 0)*

* [Slides](https://github.com/SuperV1234/bcs_thesis/blob/master/defense/slides.pdf) 


## How to compile

Requirements:

* [XeTeX](https://www.sharelatex.com/learn/XeLaTeX)

* [Pandoc](http://pandoc.org/)

* [pp](https://github.com/CDSoft/pp)

* [Python 3](https://www.python.org/)

Arch Linux packages:

* `pandoc-citeproc`

* `minted`

* `texlive-most`

* `python-pandocfilters`

Instructions:

1. Simply run the `./mk.sh` bash script.

2. If compilation is successful, `thesis.pdf` will be created in `./output`.



## Links

* **ResearchGate** entry:
[https://www.researchgate.net/publication/305730566](https://www.researchgate.net/publication/305730566_Analysis_of_entity_encoding_techniques_design_and_implementation_of_a_multithreaded_compile-time_Entity-Component-System_C14_library)

* **ECST** repository:
[https://github.com/SuperV1234/ecst](https://github.com/SuperV1234/ecst)

* **C++Now 2016** repository *(contains presentation material on ECST)*:
[https://github.com/SuperV1234/cppnow2016](https://github.com/SuperV1234/cppnow2016)

* Pandoc template repository: [https://github.com/tompollard/phd_thesis_markdown](https://github.com/tompollard/phd_thesis_markdown)
