
.. _installation:


Installation
============

PyDCOP runs on python >= 3.11.
We recommend using ``pip`` and installing pyDCOP in a
`python venv <https://docs.python.org/3/library/venv.html>`_::

  python3 -m venv ~/pydcop_env
  source ~/pydcop_env/bin/activate

Then you can simply install using pip::

  git clone https://github.com/Orange-OpenSource/pyDcop.git
  cd pyDcop
  pip install .

When developing on pyDCOP, for example to implement a new DCOP algorithm, one
would rather use the following command, which installs pyDCOP in development
mode with test dependencies::

  pip install -e .[test]

To generate documentation, you need to install the corresponding dependencies::

  pip install -e .[doc]

When building documentation locally, disable autosummary generation to avoid
rewriting committed autosummary files::

  SPHINXOPTS="-D autosummary_generate=0" make html


Additionally, for computations distribution, pyDCOP uses the
`glpk <https://www.gnu.org/software/glpk/>`_ linear program solver, which must
be installed on the system (as it is not a python library, which could be
installed as a dependency by `pip`). For example, on an Ubuntu/Debian system::

  sudo apt-get install glpk-utils

For exact centralized solves with ``pydcop solve -a pulp``, CBC is the default
PuLP backend. pyDCOP prefers a ``cbc`` executable found on ``PATH`` before
falling back to PuLP's bundled CBC solver. HiGHS can also be used with
``-p solver:highs`` when the ``highs`` executable is installed and available on
``PATH``. On macOS with Homebrew::

  brew install highs



.. note:: On many linux distribution, ``pip`` is not installed by default. On
  ubuntu for example, install using::

    sudo apt-get install python3-setuptools
    sudo apt-get install python3-pip


.. note::  When installing pyDCOP over many machines (or virtual machines),
  for a really distributed system, we recommend automating the process.
  We provide ansible playbook that can help you with this task.
  See the guide :ref:`usage_provisioning`.
