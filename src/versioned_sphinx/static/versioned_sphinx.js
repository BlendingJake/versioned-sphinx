document.addEventListener("DOMContentLoaded", documentReady);

const THEME_INJECT_POINT = {
    sphinx_rtd_theme: "section div[role='navigation']"
};

let VERSIONS;

function determineCurrentVersion() {
    const href = window.location.href;
    return VERSIONS.find((v) => href.includes(`/${v.display_name}/`));
}

function documentReady() {
    const navContainer = document.querySelector(THEME_INJECT_POINT.sphinx_rtd_theme);
    
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
    
    window.location.href = `${base}/${value}/${path}`;
}