This directory contains various example files illustrating the use of
webamc.

The [`mcq`](mcq/) directory contains some MCQ examples containing
real-life ones. Their compilation requires your tex system to be able
to locate image and tex files in directory [`tex`](tex/). On a linux
system, this can be done by setting the `TEXINPUTS` environment
variable. You can then call `webamc compile` to compile all MCQ of
this directory into a single archive `mcq-archive.zip`:

``` bash
$ export TEXINPUTS=$TEXINPUTS:/path/to/webamc/examples/tex
$ webamc compile mcq mcq-archive
```

The [`cfg`](cfg/) directory contains an example configuration file.

The [`qst`](qst/) directory contains a bunch of latex question files
that can be compiled exactly as the MCQ found in the `mcq` directory.

The [`csv`](csv/) directory contains a bunch of CSV files that can be
loaded with the `webamc loadcsv` command. Check out the
[`README`](csv/README.md) file in this directory for help.

