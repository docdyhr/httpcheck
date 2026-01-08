Contributing
============

We welcome contributions to httpcheck! This guide will help you get started.

Development Setup
-----------------

1. Fork and clone the repository:

.. code-block:: bash

   git clone https://github.com/yourusername/httpcheck.git
   cd httpcheck

2. Create a virtual environment:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3. Install in development mode:

.. code-block:: bash

   pip install -e ".[dev]"

4. Install pre-commit hooks (optional):

.. code-block:: bash

   pre-commit install

Code Quality Standards
----------------------

Pylint
~~~~~~

All code must maintain a **10.0/10 pylint score**:

.. code-block:: bash

   pylint --fail-under=10.0 httpcheck/*.py

Test Coverage
~~~~~~~~~~~~~

Maintain **>70% test coverage** (target: >80%):

.. code-block:: bash

   pytest tests/ --cov=httpcheck --cov-fail-under=70

Security
~~~~~~~~

Run security audits before committing:

.. code-block:: bash

   pip-audit
   bandit -r httpcheck/

Testing
-------

Run All Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/

Run Specific Test File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/test_cli_integration.py -v

Run with Coverage Report
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/ --cov=httpcheck --cov-report=html
   open htmlcov/index.html

Making Changes
--------------

1. **Create a feature branch**:

   .. code-block:: bash

      git checkout -b feature/my-new-feature

2. **Make your changes** following the code style

3. **Add tests** for new functionality

4. **Update documentation** if needed

5. **Run quality checks**:

   .. code-block:: bash

      pylint httpcheck/*.py
      pytest tests/ --cov=httpcheck
      pip-audit

6. **Commit your changes**:

   .. code-block:: bash

      git commit -m "feat: add new feature"

7. **Push and create a pull request**

Commit Message Format
---------------------

Use conventional commits format:

- ``feat:`` New feature
- ``fix:`` Bug fix
- ``docs:`` Documentation changes
- ``test:`` Adding/updating tests
- ``refactor:`` Code refactoring
- ``perf:`` Performance improvements
- ``chore:`` Maintenance tasks

Examples:

.. code-block:: text

   feat: add JSON output format
   fix: handle timeout errors correctly
   docs: update API documentation
   test: add CLI integration tests

Pull Request Guidelines
-----------------------

- Keep PRs focused on a single feature/fix
- Include tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass
- Maintain backward compatibility
- Add entry to CHANGELOG.md

Code Style
----------

We follow PEP 8 with these guidelines:

- Maximum line length: 100 characters
- Use type hints for function parameters
- Write docstrings for all public functions
- Use meaningful variable names
- Keep functions small and focused

Example:

.. code-block:: python

   def check_site(
       url: str,
       timeout: float = 5.0,
       retries: int = 2
   ) -> SiteStatus:
       """Check the HTTP status of a website.

       Args:
           url: The URL to check
           timeout: Request timeout in seconds
           retries: Number of retry attempts

       Returns:
           SiteStatus object with check results
       """
       # Implementation here

Testing Guidelines
------------------

- Write tests for all new features
- Use meaningful test names
- Test edge cases and error conditions
- Mock external dependencies
- Aim for >80% coverage

Example test:

.. code-block:: python

   def test_check_site_success(self, mock_request):
       """Test successful site check."""
       mock_request.return_value.status_code = 200

       status = check_site("https://example.com")

       assert status.status == "200"
       assert status.domain == "example.com"

Documentation
-------------

Update documentation when:

- Adding new features
- Changing CLI options
- Modifying public APIs
- Adding examples

Documentation is in ``docs/`` directory using reStructuredText format.

Build docs locally:

.. code-block:: bash

   cd docs
   make html
   open _build/html/index.html

Getting Help
------------

- GitHub Issues: https://github.com/docdyhr/httpcheck/issues
- Discussions: https://github.com/docdyhr/httpcheck/discussions

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.
