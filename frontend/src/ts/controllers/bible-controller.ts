import { cachedFetchJson } from "../utils/json-data";
import { shuffle } from "../utils/arrays";
import { LocalStorageWithSchema } from "../utils/local-storage-with-schema";
import { subscribe } from "../observables/config-event";
import { z } from "zod";

type BibleBook = {
  id: number;
  name: string;
  testament: "OT" | "NT";
};

type BibleVerse = {
  v: number;
  t: string;
};

type BibleBookData = {
  name: string;
  chapters: Record<string, BibleVerse[]>;
};

// Same character-length groups as original monkeytype quotes
const LENGTH_GROUPS: [number, number][] = [
  [0, 100], // 0 = short
  [101, 300], // 1 = medium
  [301, 600], // 2 = long
];

const selectedBookLS = new LocalStorageWithSchema({
  key: "bibleBook",
  schema: z.string(),
  fallback: "all",
});

let selectedBook: string = selectedBookLS.get() ?? "all";
let booksCache: BibleBook[] | null = null;
let currentVerseQueue: string[] = [];
let queueIndex = 0;

export function getSelectedBook(): string {
  return selectedBook;
}

export function getSelectedBookDisplayName(): string {
  if (selectedBook === "all") return "All Books";
  if (booksCache === null) return selectedBook;
  const book = booksCache.find(
    (b) => b.name.toLowerCase().replace(/ /g, "-") === selectedBook,
  );
  return book?.name ?? selectedBook;
}

export function setSelectedBook(bookSlug: string): void {
  selectedBook = bookSlug;
  selectedBookLS.set(bookSlug);
  currentVerseQueue = [];
  queueIndex = 0;
}

export async function getBooks(): Promise<BibleBook[]> {
  if (booksCache !== null) return booksCache;
  booksCache = await cachedFetchJson<BibleBook[]>("bible/books.json");
  return booksCache;
}

function buildQuoteText(verses: BibleVerse[]): string {
  return verses.map((v) => v.t).join(" ");
}

function generateAllPassages(data: BibleBookData): string[] {
  const texts: string[] = [];

  for (const chapter of Object.keys(data.chapters)) {
    const verses = data.chapters[chapter] as BibleVerse[];

    // Generate passages of different sizes (1 to 12 verses)
    // so we get a good spread across short/medium/long groups
    for (let i = 0; i < verses.length; ) {
      const chunkSize = 1 + Math.floor(Math.random() * 12);
      const chunk = verses.slice(i, i + chunkSize);
      const text = buildQuoteText(chunk);
      if (text.length > 10) {
        texts.push(text);
      }
      i += chunkSize;
    }
  }

  return texts;
}

function filterByQuoteLength(
  passages: string[],
  quoteLengths: number[],
): string[] {
  if (quoteLengths.length === 0) return passages;

  return passages.filter((text) => {
    const len = text.length;
    return quoteLengths.some((ql) => {
      const group = LENGTH_GROUPS[ql];
      if (group === undefined) return false;
      return len >= group[0] && len <= group[1];
    });
  });
}

async function loadPassages(
  bookSlug: string,
  quoteLengths: number[],
): Promise<string[]> {
  const data = await cachedFetchJson<BibleBookData>(`bible/${bookSlug}.json`);
  const all = generateAllPassages(data);
  const filtered = filterByQuoteLength(all, quoteLengths);

  // If filtering leaves nothing, fall back to all passages
  return filtered.length > 0 ? filtered : all;
}

export async function getRandomPassage(
  quoteLengths: number[],
): Promise<string> {
  if (
    currentVerseQueue.length === 0 ||
    queueIndex >= currentVerseQueue.length
  ) {
    if (selectedBook === "all") {
      const books = await getBooks();
      const randomBook = books[
        Math.floor(Math.random() * books.length)
      ] as BibleBook;
      const slug = randomBook.name.toLowerCase().replace(/ /g, "-");
      currentVerseQueue = await loadPassages(slug, quoteLengths);
    } else {
      currentVerseQueue = await loadPassages(selectedBook, quoteLengths);
    }
    shuffle(currentVerseQueue);
    queueIndex = 0;
  }

  const passage = currentVerseQueue[queueIndex] as string;
  queueIndex++;
  return passage;
}

// Invalidate queue when quote length changes so new filter applies
subscribe(({ key }) => {
  if (key === "quoteLength") {
    currentVerseQueue = [];
    queueIndex = 0;
  }
});
