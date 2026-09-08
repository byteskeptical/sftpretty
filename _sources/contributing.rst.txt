Contributing
============
You can contribute to the project in a number of ways. Code is always good, bugs are interesting but tests make your famous!

Bug reports or feature enhancements that include a test are given preferential treatment. So instead of voting for an issue, write a test.

Bug Reports
-----------
If you encounter a bug or some surprising behavior, please file an issue on our `tracker <https://github.com/byteskeptical/sftpretty/issues>`_.

Code
----
    #. Fork the repository `sftpretty <https://github.com/byteskeptical/sftpretty>`_
    #. Install supporting software packages and sftpretty in --editable mode

        a. Make a virtualenv, python3 -m venv .sftpretty 
        b. Clone the repo, git clone https://github.com/`username`/sftpretty
        c. Install sftpretty and it's dependencies in editable mode, python3 -m pip install -e .[dev,lint,test]

    #. Write any new tests needed and ensure existing tests continue to pass without modification.

        a. Setup CI testing for your fork. Currently testing is done on Github Actions but feel free to use the framework of your choosing.
        b. Testing features that concern chmod, chown on Windows is NOT supported. Testing compression has to be ran against a local compatible sshd and not the pytest-sftpserver plugin as it does NOT support this feature.
        c. You will need to setup an ssh daemon on your local machine and create a user: copy the contents of id_sftpretty.pub to the newly created user's authorized_keys file -- Tests that can only be ran locally are skipped using the @skip_if_ci decorator so they don't fail when the test suite runs on the CI server.

    #. Ensure that your name is added to the end of the :doc:`authors` file using the format Name <email@domain.com> (url), where the (url) portion is optional.
    #. Submit a Pull Request to the project.

Docs
----
Using Sphinx to build the docs. ``make html`` is your friend, see docstrings for details on params, etc.

Issue Priorities
----------------
This section lists the priority that will be assigned to an issue:
    #. Developer Issues
    #. Issues that have a pull request with a test(s) displaying the issue and code change(s) that satisfies the test suite
    #. Issues that have a pull request with a test(s) displaying the issue
    #. Naked pull requests - a code change request with no accompaning test
    #. An issue without a pull request with a test displaying the issue
    #. Badly documented issue with no code or test - sftpretty is not an end-user tool, it is a developer tool and it is expected that issues will be submitted like a developer and not an end-user. Issues in the realm of "the internet is broken" will be marked as invalid with a comment pointing the submitter to this section.

Testing
-------
Tests specific to an issue should be placed inside the tests/ directory and the file should be named test_issue_xx.py. The tests within that module should be named test_issue_xx or test_issue_xx_YYYYYY if more than one test exists. Pull requests should not modify existing tests with extremely rare exception. See tests/test_issue_xx.py for a template and additional context.
