This directory contains various example files illustrating the use of
webamc.

The [`mcq`](mcq/) directory contains some MCQ examples containing
real-life ones. Their compilation requires your tex system to be able
to locate image and tex files in directory [`tex`](tex/). On a linux
system, this can be done by setting the `TEXINPUTS` environment
variable. You can then call `webamc compile` to compile all MCQ of
this directory into a single archive `mcq-archive.zip`:

``` bash
$ TEXINPUTS=$TEXINPUTS:/path/to/webamc/examples/tex webamc compile mcq mcq-archive
```

The [`cfg`](cfg/) directory contains an example configuration file.

The [`qst`](qst/) directory contains a bunch of latex question files
that can be compiled exactly as the MCQ found in the `mcq` directory.

