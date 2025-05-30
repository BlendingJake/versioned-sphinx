document.addEventListener("DOMContentLoaded", documentReady);

/**
 * This will be set at the bottom of the file during the build process.
 * It is an object mapping each version's display name to the list of
 * names of the HTML files for that version. It is used to ensure that,
 * when switching to a new version, that the current file still exists
 * there. If not, it will switch to the root of the new version. Example:
 * 
 * {
 *      "0.0.1": [
 *          "examples.html",
 *          "genindex.html",
 *          "index.html",
 *      ]
 * }
 */
let FILES_PER_VERSION;

/**
 * The CSS selector indicating where the version control should be injected
 * as the first child. Predefined values are provided for certain themes and
 * can be overridden (or provided for unsupported themes) by specifying 
 * vs_inject_selector in conf.py.
 */
let THEME_INJECT_POINT;

/**
 * This will be set at the bottom of the file during the build process.
 * It is an array of objects, each which has the key 'display_name: str' and
 * 'primary: boolean', along with  all of the keys from either GitBranch 
 * or GitTag. Example:
 * 
 * [{
 *      display_name: "0.0.1",
 *      primary: false,
 *      date: "2025-05-25 21:03:33-04:00",
 *      name: "v0.0.1"
 * }]
 */
let VERSIONS;

function determineCurrentVersion() {
    const href = window.location.href;
    return VERSIONS.find((v) => href.includes(`/${v.display_name}/`));
}

function documentReady() {
    const navContainer = document.querySelector(THEME_INJECT_POINT);
    
    const div = document.createElement('div');
    div.className = "versioned-sphinx";
    navContainer.insertBefore(div, navContainer.firstChild);

    const select = document.createElement('select');
    div.appendChild(select);

    const currentVersion = determineCurrentVersion().display_name;
    new Choices(
        select,
        {
            choices: VERSIONS.map(v => ({
                label: v.display_name,
                selected: v.display_name === currentVersion,
                value: v.display_name,
            })),
            itemSelectText: '',
            shouldSort: false
        }
    );

    select.addEventListener(
        'choice',
        ({ detail }) => selectVersion(detail.value)
    );
}

function selectVersion(value) {
    const href = window.location.href;
    const currentVersion = determineCurrentVersion();
    const [base, path] = href.split(`/${currentVersion.display_name}/`);

    const destFile = path.split("#")[0];
    if (FILES_PER_VERSION[value].includes(destFile)) {
        window.location.href = `${base}/${value}/${path}`;
    } else {
        window.location.href = `${base}/${value}/index.html`;
    }
}