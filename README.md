# versioned-sphinx

Build versioned HTML documentation with sphinx by building each version from branches or tags on the repository and then combining those together with a control which can be used to switch between the various versions. The UI control is styled automatically for certain themes and can customized easily for themes which aren't already supported.


## Quick start

1. `pip install versioned-sphinx`
2. Updated `conf.py` and add `versioned_sphinx.ext` to the list
3. [Optional] Add any additional options to `conf.py` to customize version sorting, display names, etc
    ```python
    # for example, in conf.py, modify how the version is displayed
    from versioned_sphinx import GitBranch, GitTag

    def vs_display_name(branch_or_tag: GitBranch | GitTag) -> str:
        # strip off the 'v', turning 'v0.0.1' -> '0.0.1'
        return branch_or_tag.name[1:]
    ```
    * The attributes specified in version of `conf.py` in the repo at the time of running the command will be used
4. Build versions from command-line: `versioned-sphinx -p v*`
    * This matches any branches or tags starting with 'v' and assumes the git repo and sphinx project are in the current folder. You can point at a different folder by providing the `-r <repo path>` parameter
5. Open `index.html` in `docs/build`


## Dependencies

`versioned-sphinx` makes use of the [`choices.js`](https://github.com/Choices-js/Choices/tree/main?tab=readme-ov-file) library to render the select in the UI in a themeable, accessible, and dynamic manner. The library is licensed under MIT, which is the same as this package. Currently, version `11.1.0` is being used.
