import { qsr } from "../utils/dom";

const nav = qsr("header nav");
const accountButtonAndMenuEl = nav.qsr(".accountButtonAndMenu");
const loginButtonEl = nav.qsr(".textButton.view-login");

export function hide(): void {
  accountButtonAndMenuEl.addClass("hidden");
  loginButtonEl.addClass("hidden");
}

export function loading(_state: boolean): void {
  // no-op — account UI elements removed
}

export function updateName(_name: string): void {
  // no-op
}

export function updateAvatar(_avatar?: {
  discordId?: string;
  discordAvatar?: string;
}): void {
  // no-op
}

export function update(): void {
  // no-op — auth is disabled
}

export function updateFriendRequestsIndicator(): void {
  // no-op
}
