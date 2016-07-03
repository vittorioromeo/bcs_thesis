PY=python
PANDOC=pandoc

BASEDIR=$(CURDIR)
TEMPDIR=$(BASEDIR)/temp
INPUTDIR=$(BASEDIR)/source
OUTPUTDIR=$(BASEDIR)/output
TEMPLATEDIR=$(INPUTDIR)/templates
STYLEDIR=$(BASEDIR)/style
BIBFILE=$(INPUTDIR)/references.bib

pdf:
	pp -en "$(INPUTDIR)"/**/*.md > "$(TEMPDIR)"/merged.md && \
	pandoc "$(TEMPDIR)"/merged.md \
	-S \
	--standalone \
	--filter "$(BASEDIR)/pandoc-minted.py" \
	-o "$(OUTPUTDIR)/thesis.tex" \
	-H "$(STYLEDIR)/preamble.tex" \
	--template="$(STYLEDIR)/template.tex" \
	--bibliography="$(BIBFILE)" 2>pandoc.log \
	--csl="$(STYLEDIR)/ieee.csl" \
	-N \
	--verbose && \
	xelatex -shell-escape "$(OUTPUTDIR)/thesis.tex" && \
	xelatex -shell-escape "$(OUTPUTDIR)/thesis.tex" && \
	mv ./thesis.* "$(OUTPUTDIR)"

textopdf:
	xelatex -shell-escape "$(OUTPUTDIR)/thesis.tex" && \
	xelatex -shell-escape "$(OUTPUTDIR)/thesis.tex" && \
	mv ./thesis.* "$(OUTPUTDIR)"


odt:
	pp -en "$(INPUTDIR)"/**/*.md > "$(TEMPDIR)"/merged.md && \
	pandoc "$(TEMPDIR)"/merged.md \
	-S \
	--standalone \
	-o "$(OUTPUTDIR)/thesis.odt" \
	--verbose && \
	mv ./thesis.* "$(OUTPUTDIR)"

html:
	pp -en "$(INPUTDIR)"/**/*.md > "$(TEMPDIR)"/merged.md && \
	pandoc "$(TEMPDIR)"/merged.md \
	-S \
	--standalone \
	-o "$(OUTPUTDIR)/thesis.html" \
	--verbose && \
	mv ./thesis.* "$(OUTPUTDIR)"

.PHONY: pdf odt html
