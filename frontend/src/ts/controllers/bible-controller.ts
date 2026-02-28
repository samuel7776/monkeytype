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

// Theme index: theme -> book slug -> chapter -> verse numbers
type ThemeIndex = Record<string, Record<string, Record<string, number[]>>>;

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

const selectedThemeLS = new LocalStorageWithSchema({
  key: "bibleTheme",
  schema: z.string(),
  fallback: "all",
});

let selectedBook: string = selectedBookLS.get() ?? "all";
let selectedTheme: string = selectedThemeLS.get() ?? "all";
let booksCache: BibleBook[] | null = null;
let themesCache: ThemeIndex | null = null;
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

export function getSelectedTheme(): string {
  return selectedTheme;
}

export function getSelectedThemeDisplayName(): string {
  if (selectedTheme === "all") return "All Themes";
  return selectedTheme.charAt(0).toUpperCase() + selectedTheme.slice(1);
}

export function setSelectedTheme(theme: string): void {
  selectedTheme = theme;
  selectedThemeLS.set(theme);
  currentVerseQueue = [];
  queueIndex = 0;
}

export async function getBooks(): Promise<BibleBook[]> {
  if (booksCache !== null) return booksCache;
  booksCache = await cachedFetchJson<BibleBook[]>("bible/books.json");
  return booksCache;
}

export async function getThemes(): Promise<ThemeIndex> {
  if (themesCache !== null) return themesCache;
  themesCache = await cachedFetchJson<ThemeIndex>("bible/themes.json");
  return themesCache;
}

export function getThemeNames(): string[] {
  if (themesCache === null) return [];
  return Object.keys(themesCache);
}

function buildQuoteText(verses: BibleVerse[]): string {
  return verses.map((v) => v.t).join(" ");
}

function filterVersesByTheme(
  verses: BibleVerse[],
  allowedVerses: Set<number>,
): BibleVerse[] {
  return verses.filter((v) => allowedVerses.has(v.v));
}

function generateAllPassages(
  data: BibleBookData,
  themeVerseFilter: Record<string, Set<number>> | null,
): string[] {
  const texts: string[] = [];

  for (const chapter of Object.keys(data.chapters)) {
    let verses = data.chapters[chapter] as BibleVerse[];

    // If a theme filter is active, only use matching verses
    if (themeVerseFilter !== null) {
      const allowed = themeVerseFilter[chapter];
      if (allowed === undefined) continue;
      verses = filterVersesByTheme(verses, allowed);
      if (verses.length === 0) continue;
    }

    // Generate passages at multiple chunk sizes to ensure good coverage
    // across short/medium/long length groups
    const chunkSizes = [1, 2, 3, 5, 8, 12];
    for (const chunkSize of chunkSizes) {
      for (let i = 0; i < verses.length; i += chunkSize) {
        const chunk = verses.slice(i, i + chunkSize);
        const text = buildQuoteText(chunk);
        if (text.length > 10) {
          texts.push(text);
        }
      }
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

function getThemeVerseFilter(
  bookSlug: string,
): Record<string, Set<number>> | null {
  if (selectedTheme === "all" || themesCache === null) return null;

  const themeData = themesCache[selectedTheme];
  if (themeData === undefined) return null;

  const bookData = themeData[bookSlug];
  if (bookData === undefined) return null;

  const result: Record<string, Set<number>> = {};
  for (const [chapter, verses] of Object.entries(bookData)) {
    result[chapter] = new Set(verses);
  }
  return result;
}

function getBooksForTheme(): string[] | null {
  if (selectedTheme === "all" || themesCache === null) return null;

  const themeData = themesCache[selectedTheme];
  if (themeData === undefined) return null;

  return Object.keys(themeData);
}

async function loadPassagesFromBook(
  bookSlug: string,
  quoteLengths: number[],
): Promise<string[]> {
  const data = await cachedFetchJson<BibleBookData>(`bible/${bookSlug}.json`);
  const themeFilter = getThemeVerseFilter(bookSlug);
  const all = generateAllPassages(data, themeFilter);
  return filterByQuoteLength(all, quoteLengths);
}

async function loadPassages(quoteLengths: number[]): Promise<string[]> {
  const themedBooks = getBooksForTheme();

  // Determine which book slugs to try
  let bookSlugs: string[];
  if (selectedBook !== "all") {
    bookSlugs = [selectedBook];
  } else if (themedBooks !== null) {
    bookSlugs = [...themedBooks];
    shuffle(bookSlugs);
  } else {
    const books = await getBooks();
    bookSlugs = books.map((b) => b.name.toLowerCase().replace(/ /g, "-"));
    shuffle(bookSlugs);
  }

  // Try the primary book first
  const primarySlug = bookSlugs[0] as string;
  const passages = await loadPassagesFromBook(primarySlug, quoteLengths);
  if (passages.length > 0) return passages;

  // If the primary book had no matching passages, try others
  for (let i = 1; i < bookSlugs.length; i++) {
    const result = await loadPassagesFromBook(
      bookSlugs[i] as string,
      quoteLengths,
    );
    if (result.length > 0) return result;
  }

  // Last resort: load from primary book without length filter
  const data = await cachedFetchJson<BibleBookData>(
    `bible/${primarySlug}.json`,
  );
  const themeFilter = getThemeVerseFilter(primarySlug);
  return generateAllPassages(data, themeFilter);
}

export async function getRandomPassage(
  quoteLengths: number[],
): Promise<string> {
  // Ensure themes are loaded
  await getThemes();

  if (
    currentVerseQueue.length === 0 ||
    queueIndex >= currentVerseQueue.length
  ) {
    currentVerseQueue = await loadPassages(quoteLengths);
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
