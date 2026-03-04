import "@testing-library/jest-dom/vitest";

// -----------------------------------------------------------------------
// Node.js 25 ships a built-in `localStorage` global that is a plain object
// without the Web Storage API methods (setItem, getItem, removeItem, clear).
// This shadows the localStorage that jsdom would normally provide, breaking
// any code (source or test) that calls localStorage.setItem() etc.
//
// Fix: replace globalThis.localStorage with a spec-compliant in-memory
// Storage implementation so the source code under test works correctly.
// -----------------------------------------------------------------------
class MemoryStorage implements Storage {
  private store = new Map<string, string>();

  get length(): number {
    return this.store.size;
  }

  clear(): void {
    this.store.clear();
  }

  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  key(index: number): string | null {
    const keys = Array.from(this.store.keys());
    return keys[index] ?? null;
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }

  // Support bracket notation (storage["key"])
  [name: string]: unknown;
}

// Only patch if the current localStorage is missing the standard API
if (typeof globalThis.localStorage?.setItem !== "function") {
  const storage = new MemoryStorage();
  Object.defineProperty(globalThis, "localStorage", {
    value: storage,
    writable: true,
    configurable: true,
  });
}
