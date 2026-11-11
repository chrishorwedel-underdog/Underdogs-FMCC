import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// what the game calls you (set in setup, editable in Settings)
export const useAddress = () => {
  const { data } = useQuery({ queryKey: ["state"], queryFn: () => api.get("/state").then((r) => r.data) });
  return data?.address || "Boss";
};
