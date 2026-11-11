import { api } from "@/lib/api";

export const autoDownload = async (path, name) => {
  try {
    const r = await api.get(path, { responseType: "blob" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(r.data);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  } catch {
    // the file stays available from its list's File button
  }
};
