/// <reference types="vite/client" />

/**
 * Vite environment variable type declarations.
 *
 * @module vite-env
 */

interface ImportMetaEnv {
  /** Backend API base URL. */
  readonly VITE_API_BASE_URL: string;
  /** Backend API authentication key. */
  readonly VITE_API_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
