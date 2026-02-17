import { ConfigValue, QuoteLength } from "@monkeytype/schemas/configs";
import Config from "../config";
import * as ConfigEvent from "../observables/config-event";
import { getActivePage } from "../signals/core";
import { qs, qsa } from "../utils/dom";

export function show(): void {
  qs("#testConfig")?.removeClass("invisible");
  qs("#mobileTestConfigButton")?.removeClass("invisible");
}

export function hide(): void {
  qs("#testConfig")?.addClass("invisible");
  qs("#mobileTestConfigButton")?.addClass("invisible");
}

export async function instantUpdate(): Promise<void> {
  qs("#testConfig .quoteLength")?.show();
  updateActiveExtraButtons("quoteLength", Config.quoteLength);
}

function updateActiveExtraButtons(key: string, value: ConfigValue): void {
  if (key === "quoteLength") {
    qsa("#testConfig .quoteLength .textButton")?.removeClass("active");

    (value as QuoteLength[]).forEach((ql) => {
      qs(
        "#testConfig .quoteLength .textButton[quoteLength='" + ql + "']",
      )?.addClass("active");
    });
  }
}

let ignoreConfigEvent = false;

ConfigEvent.subscribe(({ key, newValue }) => {
  if (key === "fullConfigChange") {
    ignoreConfigEvent = true;
  }
  if (key === "fullConfigChangeFinished") {
    ignoreConfigEvent = false;

    void instantUpdate();
  }

  if (ignoreConfigEvent) return;

  if (getActivePage() !== "test") return;
  if (key === "quoteLength") {
    if (newValue !== undefined) {
      updateActiveExtraButtons(key, newValue);
    }
  }
});
