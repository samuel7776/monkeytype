import * as BibleController from "../controllers/bible-controller";
import * as ManualRestart from "../test/manual-restart-tracker";
import * as TestLogic from "../test/test-logic";
import { blurInputElement } from "../input/input-element";

type BibleBook = {
  id: number;
  name: string;
  testament: "OT" | "NT";
};

let books: BibleBook[] = [];
let isOpen = false;

function getDropdown(): HTMLElement | null {
  return document.querySelector("#bibleBookDropdown");
}

function getOverlay(): HTMLElement | null {
  return document.querySelector("#bibleBookDropdownOverlay");
}

function updateButtonText(): void {
  const bookName = document.querySelector("#bibleBookButton .bookName");
  if (bookName !== null) {
    bookName.textContent = BibleController.getSelectedBookDisplayName();
  }
}

function renderBookList(filter = ""): void {
  const dropdown = getDropdown();
  if (dropdown === null) return;

  const listEl = dropdown.querySelector(".bookList");
  if (listEl === null) return;

  const selectedBook = BibleController.getSelectedBook();
  const lowerFilter = filter.toLowerCase();

  const filtered =
    filter !== ""
      ? books.filter((b) => b.name.toLowerCase().includes(lowerFilter))
      : books;

  let html = `<div class="bookItem${selectedBook === "all" ? " selected" : ""}" data-slug="all">All Books</div>`;

  for (const book of filtered) {
    const slug = book.name.toLowerCase().replace(/ /g, "-");
    const isSelected = selectedBook === slug;
    html += `<div class="bookItem${isSelected ? " selected" : ""}" data-slug="${slug}">${book.name}</div>`;
  }

  listEl.innerHTML = html;
}

function open(): void {
  const dropdown = getDropdown();
  if (dropdown === null) return;

  let overlay = getOverlay();
  if (overlay === null) {
    overlay = document.createElement("div");
    overlay.id = "bibleBookDropdownOverlay";
    document.body.appendChild(overlay);
  }

  dropdown.classList.remove("hidden");
  isOpen = true;

  // Blur the typing test input so keystrokes don't go there
  blurInputElement();

  renderBookList();

  const input = dropdown.querySelector<HTMLInputElement>("#bibleBookSearch");
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

function selectBook(slug: string): void {
  BibleController.setSelectedBook(slug);
  updateButtonText();
  close();
  ManualRestart.set();
  TestLogic.restart();
}

export async function init(): Promise<void> {
  books = await BibleController.getBooks();
  updateButtonText();

  const button = document.querySelector("#bibleBookButton");
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

    const input = dropdown.querySelector<HTMLInputElement>("#bibleBookSearch");
    if (input !== null) {
      input.addEventListener("input", () => {
        renderBookList(input.value);
      });
      input.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          close();
        } else if (e.key === "Enter") {
          const firstItem = dropdown.querySelector(".bookList .bookItem");
          if (firstItem !== null) {
            const slug = firstItem.getAttribute("data-slug");
            if (slug !== null && slug !== "") selectBook(slug);
          }
        }
      });
    }

    dropdown.addEventListener("click", (e) => {
      const target = (e.target as HTMLElement).closest(".bookItem");
      if (target !== null) {
        const slug = target.getAttribute("data-slug");
        if (slug !== null && slug !== "") selectBook(slug);
      }
    });
  }
}
