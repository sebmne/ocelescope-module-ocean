import { isAxiosError } from "axios";
import { useState } from "react";
import { exportSocel } from "../../api/socel";
import { useSelectedOcel } from "../useSelectedOcel";

/**
 * Downloads the selected sOCEL as SQLite, its tables as the thesis declares them.
 * The download is a file, so an error arrives as one too: its message is read
 * out of it here.
 */
export function useExportSocel() {
  const { id } = useSelectedOcel();
  const [error, setError] = useState<string>();
  const [isPending, setPending] = useState(false);

  const download = async (fileName: string) => {
    if (!id) return;
    setPending(true);
    setError(undefined);
    try {
      const blob = await exportSocel(id);
      const url = URL.createObjectURL(blob);
      Object.assign(document.createElement("a"), { href: url, download: fileName }).click();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setError(await messageOf(caught));
    } finally {
      setPending(false);
    }
  };

  return { download, isPending, error };
}

async function messageOf(error: unknown): Promise<string> {
  const fallback = "Downloading the sOCEL failed.";
  if (!isAxiosError(error) || !(error.response?.data instanceof Blob)) return fallback;
  try {
    const body = JSON.parse(await error.response.data.text()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : fallback;
  } catch {
    return fallback;
  }
}
