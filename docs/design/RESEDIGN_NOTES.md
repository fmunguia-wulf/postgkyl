I'm reopening this DR after discussing with Ammar that the key issue with the one before was the direct inclusion of Claude's output in the text. This text is entirely human-written, with Claude's opinion in a file, if you're interested.

I was inspired by a YouTube video about readable code.
https://m.youtube.com/watch?v=SJocPm2E8eQ
Part of my most recent frustration comes from the disconnect between the script pgkyl and the command-line pgkyl, which have very different interfaces. This leads people to align with either one or the other. It would be great to have a more command-line-like interface we could use in pgkyl, similar to this. In contrast to my earlier DRs, I'm suggesting thinking about the script mode pgkyl from a top-down approach. It will benefit us to think about the final scripts we want to write, rather than an API-first approach. I know this is a standard goal, ideal, and objective for our projects, but I don't think it's been applied well to script pgkyl. 

In a Python script, we could plot some data like

```python
import postgkeyll as pg

pg.load('filename').select(z0=0.0).plot()
```

This could also write the common data object to avoid using activate and tagging.

```python
import postgkeyll as pg

data1 = pg.load('filename').select(z0=0.0)
data2 = pg.load('file2').evaluate('f 5 +').select(z0=0.0)
pg.plot(data1.and(data2))
pg.print(data1)
```

Here, the `and()` method simply adds data1 and data2 to the same stack for pg plotting.

The goal is to construct a "language" for how to write pgkyl scripts, similar to the YouTube video describes. In practice, this could be an object-oriented wrapper for our underlying functionality.

We can define a dunder method for these data classes to perform regular Python operations on these objects (print, add, multiply, divide). This would make manipulation more intuitive.

Additionally, we can use this interface to interact with existing structures like numpy. We can (and should) put guardrails on these methods so that we can't perform NumPy operations on DG non-interpolated data.

```python
import postgkeyll as pg
import numpy as np
import matplotlib as plt

a = pg.load('file_a').interp()
b = pg.load('file_b').interp()
c = np.sqrt(a**2 + b**2)
plt.plot(c.grid, c)
```

Here is what Claude came up with for a plan of structuring the API. It seems interesting.

[READABLE_API.md.rtf](https://github.com/user-attachments/files/29266719/READABLE_API.md.rtf)

These are just ideas for a scripting interface, and I'm very open to ideas contributing to this script-first approach.

The interface with the CLI is very, very simple. The driver of Postgkeyll, in this case, is a master class that has methods for the commands. The commands can be called from these objects. The CLI wraps the master object using click (I learned recently that `Typer` is the modernized version of click). So the layer here sits between the commands/ and click, while the current structure has the commands orchestrated with click.

Additionally, this master class should be chock-full of examples that are verified through CI. This way, it's very obvious how to use the package.