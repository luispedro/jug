#!/usr/bin/zsh
function build() {
    input=$1
    mkdir -p .$input.tex_files
    cd .$input.tex_files
    TEXINPUTS=..:../../common/:../../common/cmu-beamer/:.:../images/:../figures/: pdflatex presentation
    cp $input.pdf ..
    cd ..
}
build presentation

