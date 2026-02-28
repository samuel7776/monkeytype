import * as BibleController from "../controllers/bible-controller";
import * as ManualRestart from "../test/manual-restart-tracker";
import * as TestLogic from "../test/test-logic";
import { blurInputElement } from "../input/input-element";

let themeNames: string[] = [];
let isOpen = false;

function getDropdown(): HTMLElement | null {
  return document.querySelector("#bibleThemeDropdown");
}

function getOverlay(): HTMLElement | null {
  return document.querySelector("#bibleThemeDropdownOverlay");
}

function updateButtonText(): void {
  const themeName = document.querySelector("#bibleThemeButton .themeName");
  if (themeName !== null) {
    themeName.textContent = BibleController.getSelectedThemeDisplayName();
  }
}

function renderThemeList(filter = ""): void {
  const dropdown = getDropdown();
  if (dropdown === null) return;

  const listEl = dropdown.querySelector(".themeList");
  if (listEl === null) return;

  const selectedTheme = BibleController.getSelectedTheme();
  const lowerFilter = filter.toLowerCase();

  const filtered =
    filter !== ""
      ? themeNames.filter((t) => t.toLowerCase().includes(lowerFilter))
      : themeNames;

  let html = `<div class="themeItem${selectedTheme === "all" ? " selected" : ""}" data-theme="all">All Themes</div>`;

  for (const theme of filtered) {
    const displayName = theme.charAt(0).toUpperCase() + theme.slice(1);
    const isSelected = selectedTheme === theme;
    html += `<div class="themeItem${isSelected ? " selected" : ""}" data-theme="${theme}">${displayName}</div>`;
  }

  listEl.innerHTML = html;
}

function open(): void {
  const dropdown = getDropdown();
  if (dropdown === null) return;

  let overlay = getOverlay();
  if (overlay === null) {
    overlay = document.createElement("div");
    overlay.id = "bibleThemeDropdownOverlay";
    document.body.appendChild(overlay);
  }

  dropdown.classList.remove("hidden");
  isOpen = true;

  blurInputElement();

  renderThemeList();

  const input = dropdown.querySelector<HTMLInputElement>("#bibleThemeSearch");
  if (input !== null) {
    input.value = "";
    input.focus();
  }

  overlay.addEventListener("click", close);
}

function close(): void {
  const dropdown = getDropdown();
  if (dropdown !== null) {
    dropdown.classList.add("hidden");
  }

  const overlay = getOverlay();
  if (overlay !== null) {
    overlay.remove();
  }

  isOpen = false;
}

function selectTheme(theme: string): void {
  BibleController.setSelectedTheme(theme);
  updateButtonText();
  close();
  ManualRestart.set();
  TestLogic.restart();
}

export async function init(): Promise<void> {
  await BibleController.getThemes();
  themeNames = BibleController.getThemeNames();
  updateButtonText();

  const button = document.querySelector("#bibleThemeButton");
  button?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (isOpen) {
      close();
    } else {
      open();
    }
  });

  const dropdown = getDropdown();
  if (dropdown !== null) {
    // Stop all keyboard events from reaching the global test handlers
    dropdown.addEventListener("keydown", (e) => {
      e.stopPropagation();
    });
    dropdown.addEventListener("keyup", (e) => {
      e.stopPropagation();
    });
    dropdown.addEventListener("keypress", (e) => {
      e.stopPropagation();
    });

    const input = dropdown.querySelector<HTMLInputElement>("#bibleThemeSearch");
    if (input !== null) {
      input.addEventListener("input", () => {
        renderThemeList(input.value);
      });
      input.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          close();
        } else if (e.key === "Enter") {
          const firstItem = dropdown.querySelector(".themeList .themeItem");
          if (firstItem !== null) {
            const theme = firstItem.getAttribute("data-theme");
            if (theme !== null && theme !== "") selectTheme(theme);
          }
        }
      });
    }

    dropdown.addEventListener("click", (e) => {
      const target = (e.target as HTMLElement).closest(".themeItem");
      if (target !== null) {
        const theme = target.getAttribute("data-theme");
        if (theme !== null && theme !== "") selectTheme(theme);
      }
    });
  }
}
