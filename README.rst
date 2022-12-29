Ningen 0.4.0 - Ninja Build Generation
=====================================

.. image:: https://readthedocs.org/projects/ningen/badge/?version=latest
    :target: https://ningen.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

This package allows a Python script to use file system operations (such as ``glob``) and/or apply
any other logic (such as reading structured configuration files) to generate a ``build.ninja`` file.

This isn't intended to replace "high level" build systems such as ``cmake``. Rather, think of it as
replacing the clunky GNU ``make`` language with Python.

Yes, ``ninja`` does provide the ``ninja_syntax`` module which already does this. The added value of
``ningen`` is:

* Convenience functions for pattern-based build file generation.

* Allow overriding build statements (which complements the pattern-based approach).

Installation
------------

Just ``pip install ningen`` (or the equivalent in whatever Python environment you are using).

Usage
-----

The ``Writer`` class is similar to the one in ``ninja_syntax``. Two additional utility functions are
provided: ``foreach`` for iterating on all combinations of several variables, possibly extracting
them from existing file names; and ``expand`` for generating formatted strings using all the
variable combinations.

For example:

.. code-block:: python

    import ningen as ng

    # Similarly to ninja_syntax writer, but internally buffers everything:
    writer = ng.Writer()

    modes = ['debug', 'release']
    objects = []
    writer.rule('compile_debug', ...)
    writer.rule('compile_release', ...)

    # Ningen provides the "foreach" function,
    # which iterates on existing files and/or variable values:
    for c in ng.foreach('src/{*name}.cc', mode=modes):
        objects.append(name)
        writer.build(f'obj/{c.mode}/{c.name}.o', f'compile_{c.mode}',
                     inputs=[c.path, ...], ...)

    # Since it buffers the data, ningen allows overriding previous build statements:
    writer.rule('special_compile_debug', ...)
    writer.build('obj/debug/special.o', 'special_compile_gcc',
                 inputs=['src/special.cc', ...], ..., override=True)

    # Ningen also provides the "expand" function which formats multiple strings:
    for mode in modes:
        writer.build('bin/{mode}/program', f'link_{mode}',
                     inputs=ng.expand('obj/{mode}/{object}.o',
                                      mode=mode, object=objects))

    # Actually write the buffered ninja build file (by default, to "build.ninja"):
    writer.write()
