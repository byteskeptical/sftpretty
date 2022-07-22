Contributing
============
You can contribute to the project in a number of ways. Code is always good, bugs are interesting but tests make your famous!

Bug reports or feature enhancements that include a test are given preferential treatment. So instead of voting for an issue, write a test.

Code
-----
    1. Fork the repository `sftpretty <https://github.com/byteskeptical/sftpretty>`_
    2. Install supporting software packages and sftpretty in --editable mode
      a. Make a virtualenv, clone the repos, install the deps from pip install -r requirements-dev.txt
      b. Install sftpretty in editable mode, pip install -e .
    3. Write any new tests needed and ensure existing tests continue to pass without modification.
      a. Setup CI testing for your Fork. Currently testing is done on travis but feel free to use the testing framework of your choosing.
      b. No tests are run against a public SFTP server. Keeping a server available was/is problematic and made for brittle testing. Because of this, we now use the pytest-sftpserver plugin for many tests. Testing features the concern authentication or authorization, i.e. different login types, chmod, chown have to be run against a local sshd and not the plugin as it does NOT support these types of tests.
      c. You will need to setup an ssh daemon on your local machine and create a user: test with password of test1357 -- Tests that can only be run locally are skipped using the @skip_if_ci decorator so they don't fail when the test suite is run on the CI server.
    4. Ensure that your name is added to the end of the :doc:`authors` file using the format Name <email@domain.com> (url), where the (url) portion is optional.
    5. Submit a Pull Request to the project.

Docs
-----
Using sphinx to build the docs. Make html is your friend, see docstrings for details on params, etc.

Bug Reports
-----------
If you encounter a bug or some surprising behavior, please file an issue on our `tracker <https://github.com/byteskeptical/sftpretty/issues>`_

Issue Priorities
----------------
This section lists the priority that will be assigned to an issue:
    1. Developer Issues
    2. Issues that have a pull request with a test(s) displaying the issue and code change(s) that satisfies the test suite
    3. Issues that have a pull request with a test(s) displaying the issue
    4. Naked pull requests - a code change request with no accompaning test
    5. An issue without a pull request with a test displaying the issue
    6. Badly documented issue with no code or test - sftpretty is not an end-user tool, it is a developer tool and it is expected that issues will be submitted like a developer and not an end-user. Issues in the realm of "the internet is broken" will be marked as invalid with a comment pointing the submitter to this section.

Testing
--------
Tests specific to an issue should be put in the tests/ directory and the module should be named test_issue_xx.py The tests within that module should be named test_issue_xx or test_issue_xx_YYYYYY if more than one test. Pull requests should not modify existing tests (exceptions apply). See tests/test_issue_xx.py for a template and further explanation.
