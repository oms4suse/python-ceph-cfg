This is a python module for ceph configuration and deployment.

This python module is intended to be reused by any tool that automates the
install of ceph.

All methods in this module are intended to be atomic and idempotent. Some state
changes are in practice made up of many steps, but will verify that all stages
have succeeded before presenting the result to the caller. Most functions are
fully idempotent in operation so can be repeated or retried as often as
necessary without causing unintended effects. This is so clients of this module
do not need to keep track of whether the operation was already performed or not.
Some methods do depend upon the successful completion of other methods. While
not strictly idempotent, this is considered acceptable modules having
dependencies on other methods operation should present clear error messages.

This python module was originally part of a salt execution module for configuring
ceph on large clusters but it became clear that the code was reusable without
salt.

For the original use case of salt configuration of ceph a making this module a
stand alone library helps reuse of code for the execution and state functions
without excessive state rediscovery.

Installation
------------

This library makes use of standard setuptools functionality.

    python setup.py install

Code layout
-----------

The code is structured with basic methods calling 3 main class types.

1. Models

This stores all the gathered configuration on the node to apply the function.

2. Loaders

These objects are used to update the Model.

3. Presenters

These objects are used to present the data in the model to the API users.

Unit tests
----------

This code base is tested with the tox framework. All tests are in the directory:

    ceph_cfg/tests/

To run all tests please run:

    tox

Each test can be indevidually run an example is shown here:

    py.test ceph_cfg/tests/test_utils_is_valid_base64.py 

Submitting Patches
------------------
Please add test cases to cover any code you add. You can test your changes
by running ``tox`` (You will also need ``mock`` and ``pytest`` ) from inside
the git clone

When creating a commit message please use ``git commit -s`` or otherwise add
``Signed-off-by: Your Name <email@address.dom>`` to your commit message.

Patches can then be submitted by a pull request on GitHub.
