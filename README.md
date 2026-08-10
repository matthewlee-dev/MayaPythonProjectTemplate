<a id="readme-top"></a>

<div align="center">


<!-- PROJECT LOGO -->
<br />
  <a href="https://github.com/matthewlee-dev/MayaPythonProjectTemplate">
    <img src="docs/resources/images/maya_python_logo.png" alt="MayaPythonLogo" width="175" height="175">
  </a>

[![Python][python_3-shield]][python-url]
[![Maya][maya-shield]][maya-url]
[![GitHub Actions][github-actions-shield]][github-actions-url]

<h3 align="center">Maya Python Project Template</h3>

  <p align="center">
    A GitHub template for Maya Python tools<br>
    <a href="https://github.com/matthewlee-dev/MayaPythonProjectTemplate/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/matthewlee-dev/MayaPythonProjectTemplate/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

> Example project built using this template can be found [here](https://github.com/matthewlee-dev/locator_creator). 

## HOW TO USE THIS TEMPLATE

### DO NOT FORK this is meant to be used from [Use this template][use-template-link] feature.

1. Click on [Use this template][use-template-link] button.
2. Give a name and description to the new project (e.g. my_awesome_project, please use all lowercase and underscores separation for repo names).
3. GitHub Actions will process the template and commit to the new repo, this may take a few minutes. Check the progress in the Actions tab of the new repository.
4. Once setup is complete, clone the new project and start coding!

> NOTE: WAIT until first CI run on GitHub actions before cloning the new project. This will be kicked off automatically after creating the new repo from the template, and should take a couple of minutes to complete.

## What is included in this template?
* Basic project structure.
* [README.md](_README) and [CONTRIBUTING](CONTRIBUTING.md) templates.
* Bug report and feature request templates.
* Continuous integration using [GitHub Actions][github-actions-url] with jobs to:
  * [Run integration tests](.github/workflows/reusable-maya-tests.yml) across a range of Maya versions in isolated Docker containers. 
    * `Note: You should hold a valid Maya license.`
  * [Enforce coding standards](.github/workflows/reusable-static-analysis.yml) with [pylint](https://pypi.org/project/pylint/), [black](https://github.com/psf/black), and [mypy](https://mypy.readthedocs.io/en/stable/).
  * [Build and deploy documentation](.github/workflows/reusable-build-and-deploy-docs.yml) to GitHub pages with [mkdocs](https://www.mkdocs.org/).
  * [Automated releases](.github/workflows/ci-release.yml) using Python Semantic Versioning (optional).


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments
* This project uses Docker images courtesy of [mottosso/docker-maya](https://github.com/mottosso/docker-maya).
* Inspiration taken from both:
  * [python-project-template](https://github.com/rochacbruno/python-project-template/tree/main).
  * [Best-README-Template](https://github.com/othneildrew/Best-README-Template).


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

<!-- Python -->
[python_3-shield]: https://img.shields.io/badge/Python-3.X-grey?logo=python&logoColor=ffdd54&labelColor=%233670A0
[python-url]: https://python.org/
[pytest-shield]: https://img.shields.io/badge/tests-pytest-%230A9EDC
[pytest-url]: https://docs.pytest.org/
[github-actions-shield]: https://img.shields.io/badge/GitHub%20Actions-%232671E5?logo=githubactions&logoColor=white
[github-actions-url]: https://github.com/features/actions

<!-- Maya -->
[maya-shield]: https://img.shields.io/badge/Autodesk-Maya-%2337A5CC?logo=autodeskmaya&logoColor=%2337A5CC
[maya-url]: https://www.autodesk.com/nz/products/maya/overview

<!-- template links -->
[use-template-link]: https://github.com/matthewlee-dev/MayaPythonProjectTemplate/generate
