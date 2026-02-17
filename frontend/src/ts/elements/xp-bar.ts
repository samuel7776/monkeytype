// XP bar elements have been removed from the DOM.
// These are no-op stubs to avoid crashes from existing callsites.

export async function skipBreakdown(): Promise<void> {
  // no-op
}

export function setXp(_xp: number): void {
  // no-op
}

export async function update(
  _currentXp: number,
  _addedXp: number,
  _breakdown?: unknown,
): Promise<void> {
  // no-op
}
