import { useRef, useState } from "react";
import { createEmptyRule } from "./ruleUtils";
import type { EmissionRule } from "./types";

export function useEmissionRules() {
  const [rules, setRules] = useState<EmissionRule[]>([]);
  const nextId = useRef(1);

  const addRule = () => {
    const id = nextId.current++;
    setRules((rules) => [...rules, createEmptyRule(id)]);
    return id;
  };

  const updateRule = (id: number, changes: Partial<EmissionRule>) =>
    setRules((rules) => rules.map((r) => (r.id === id ? { ...r, ...changes } : r)));

  const removeRule = (id: number) =>
    setRules((rules) => rules.filter((r) => r.id !== id));

  return [rules, addRule, updateRule, removeRule] as const;
}
