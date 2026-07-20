/** Global nav and docs sidebar toggles. */
const toggle = document.querySelector(".nav-toggle");
const links = document.getElementById("global-nav-links");

if (toggle && links) {
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  });

  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open menu");
    });
  });
}

const docsToggle = document.querySelector(".docs-sidebar-toggle");
const docsNav = document.getElementById("docs-sidebar-nav");

if (docsToggle && docsNav) {
  docsToggle.addEventListener("click", () => {
    const open = docsNav.classList.toggle("is-open");
    docsToggle.setAttribute("aria-expanded", String(open));
  });
}
