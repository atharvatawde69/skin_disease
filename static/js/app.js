/* DermaScan interface behaviour: file preview and validation, loading state, heatmap slider. */
(function () {
  "use strict";

  var MAX_BYTES = 10 * 1024 * 1024;

  // ---- light / dark theme: the page already has data-theme set (saved choice or system default) ----
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function storedTheme() {
    try { return localStorage.getItem("theme"); } catch (e) { return null; }
  }

  function describeToggle() {
    var dark = root.getAttribute("data-theme") === "dark";
    toggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    toggle.setAttribute("title", dark ? "Switch to light theme" : "Switch to dark theme");
  }

  toggle.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) { /* private mode: the choice just isn't remembered */ }
    describeToggle();
  });

  // until the visitor makes a choice, keep following the system setting
  if (media && media.addEventListener) {
    media.addEventListener("change", function (event) {
      if (!storedTheme()) {
        root.setAttribute("data-theme", event.matches ? "dark" : "light");
        describeToggle();
      }
    });
  }
  describeToggle();

  var form = document.getElementById("upload-form");
  var input = document.getElementById("file-input");
  var zone = document.getElementById("dropzone");
  var title = document.getElementById("dz-title");
  var hint = document.getElementById("dz-hint");
  var thumb = document.getElementById("dz-thumb");
  var errorBox = document.getElementById("form-error");
  var button = document.getElementById("submit-btn");
  var buttonLabel = document.getElementById("submit-label");

  var defaults = {
    title: title.textContent,
    hint: hint.textContent,
    thumb: thumb.innerHTML,
    button: buttonLabel.textContent
  };
  var previewUrl = null;

  function resetFile() {
    input.value = "";
    title.textContent = defaults.title;
    hint.textContent = defaults.hint;
    thumb.innerHTML = defaults.thumb;
    if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
  }

  input.addEventListener("change", function () {
    errorBox.textContent = "";
    var file = input.files[0];
    if (!file) { resetFile(); return; }
    if (!file.type || file.type.indexOf("image/") !== 0) {
      errorBox.textContent = "Please choose an image file (PNG or JPG).";
      resetFile();
      return;
    }
    if (file.size > MAX_BYTES) {
      errorBox.textContent = "That file is larger than 10 MB.";
      resetFile();
      return;
    }
    if (previewUrl) { URL.revokeObjectURL(previewUrl); }
    previewUrl = URL.createObjectURL(file);
    title.textContent = file.name;
    hint.textContent = (file.size / 1024 / 1024).toFixed(2) + " MB. Select Analyze to continue.";
    var img = document.createElement("img");
    img.alt = "Preview of the selected image";
    img.src = previewUrl;
    thumb.innerHTML = "";
    thumb.appendChild(img);
  });

  ["dragenter", "dragover"].forEach(function (name) {
    zone.addEventListener(name, function () { zone.classList.add("drag"); });
  });
  ["dragleave", "drop"].forEach(function (name) {
    zone.addEventListener(name, function () { zone.classList.remove("drag"); });
  });

  form.addEventListener("submit", function (event) {
    if (!input.files.length) {
      event.preventDefault();
      errorBox.textContent = "Please choose an image first.";
      return;
    }
    button.classList.add("loading");
    button.disabled = true;
    buttonLabel.textContent = "Analyzing";
  });

  // returning with the Back button must not leave the button stuck in its loading state
  window.addEventListener("pageshow", function () {
    button.classList.remove("loading");
    button.disabled = false;
    buttonLabel.textContent = defaults.button;
  });

  var slider = document.getElementById("heat-slider");
  var compare = document.getElementById("compare");
  if (slider && compare) {
    slider.addEventListener("input", function () {
      compare.style.setProperty("--o", slider.value / 100);
    });
  }

  var result = document.getElementById("result");
  if (result) {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    result.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
})();
