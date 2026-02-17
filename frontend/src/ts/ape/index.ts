import { envConfig } from "virtual:env-config";
import { buildClient } from "./adapters/ts-rest-adapter";
import { contract } from "@monkeytype/contracts";

const BASE_URL = envConfig.backendUrl;

const tsRestClient = buildClient(contract, BASE_URL, 10_000);

// API Endpoints
const Ape = {
  ...tsRestClient,
};

export default Ape;
