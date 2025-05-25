# versioned-sphinx
Versioned documentation with Sphinx

### Dependencies

`versioned-sphinx` makes use of the [`choices.js`](https://github.com/Choices-js/Choices/tree/main?tab=readme-ov-file) library to render the select in the UI in a themeable, accessible, and dynamic manner. The library is licensed under MIT, which is the same as this package. Currently, version `11.1.0` is being used.

### TODO
- [x] Build interaction with git
- [x] Build loop for building sphinx for each branch/tag
- [ ] Interpret and combine index files to know when a link can be carried to a different version
- [x] Add hooks into conf.py to allow specifying which branches/tags to match, how to format names, and sorting
- [ ] Combine all versions and set primary
- [ ] Build HTML/CSS/JS for version control
- [ ] Add caching
