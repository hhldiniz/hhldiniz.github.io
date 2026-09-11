/* Progressive enhancement for the project showcase.
   Without JavaScript the page still renders every project; this script only
   adds the theme toggle plus client-side search, language filter and sorting. */
(function () {
  "use strict";

  /* ------------------------------------------------------------- theme -- */

  var STORAGE_KEY = "portfolio-theme";
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      /* Private mode or blocked storage: the choice just won't be remembered. */
    }
  }

  var stored = null;
  try {
    stored = window.localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    stored = null;
  }

  if (stored === "light" || stored === "dark") {
    root.setAttribute("data-theme", stored);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
    root.setAttribute("data-theme", "light");
  }

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      applyTheme(root.getAttribute("data-theme") === "light" ? "dark" : "light");
    });
  }

  /* ------------------------------------------------------------ filters -- */

  var grid = document.querySelector("[data-grid]");
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll("[data-repo]"));
  if (!cards.length) return;

  var toolbar = document.querySelector("[data-toolbar]");
  var filters = document.querySelector("[data-filters]");
  var searchInput = document.querySelector("[data-search]");
  var sortSelect = document.querySelector("[data-sort]");
  var resultCount = document.querySelector("[data-result-count]");
  var emptyState = document.querySelector("[data-empty]");

  [toolbar, filters, resultCount].forEach(function (element) {
    if (element) element.hidden = false;
  });

  var state = { query: "", language: "", sort: "recent" };

  var comparators = {
    recent: function (a, b) {
      return (b.getAttribute("data-pushed") || "").localeCompare(a.getAttribute("data-pushed") || "");
    },
    stars: function (a, b) {
      var diff = Number(b.getAttribute("data-stars")) - Number(a.getAttribute("data-stars"));
      return diff !== 0 ? diff : comparators.recent(a, b);
    },
    name: function (a, b) {
      return (a.getAttribute("data-name") || "").localeCompare(b.getAttribute("data-name") || "");
    }
  };

  function matches(card) {
    if (state.language && card.getAttribute("data-language") !== state.language) return false;
    if (!state.query) return true;
    return (card.getAttribute("data-text") || "").indexOf(state.query) !== -1;
  }

  function render() {
    var visible = 0;

    cards.forEach(function (card) {
      var show = matches(card);
      card.hidden = !show;
      if (show) visible += 1;
    });

    var ordered = cards.slice().sort(comparators[state.sort] || comparators.recent);
    var fragment = document.createDocumentFragment();
    ordered.forEach(function (card) {
      fragment.appendChild(card);
    });
    grid.appendChild(fragment);

    if (resultCount) {
      resultCount.textContent =
        visible === cards.length
          ? "Showing all " + cards.length + " projects"
          : "Showing " + visible + " of " + cards.length + " projects";
    }
    if (emptyState) emptyState.hidden = visible !== 0;
  }

  if (searchInput) {
    searchInput.addEventListener("input", function (event) {
      state.query = event.target.value.trim().toLowerCase();
      render();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", function (event) {
      state.sort = event.target.value;
      render();
    });
  }

  if (filters) {
    filters.addEventListener("click", function (event) {
      var chip = event.target.closest("[data-language]");
      if (!chip) return;

      var language = chip.getAttribute("data-language");
      /* Clicking the active language clears the filter. */
      state.language = state.language === language ? "" : language;

      Array.prototype.forEach.call(filters.querySelectorAll("[data-language]"), function (button) {
        var isActive = button.getAttribute("data-language") === state.language;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
      });

      render();
    });
  }

  render();
})();
