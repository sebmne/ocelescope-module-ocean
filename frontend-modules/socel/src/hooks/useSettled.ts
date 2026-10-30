import { useEffect, useState } from "react";

/** The value once it has stopped changing for `ms`: what is asked of the
 * backend while the user types, so not every keystroke is a request. */
export function useSettled<T>(value: T, ms: number) {
  const [settled, setSettled] = useState(value);
  const key = JSON.stringify(value);
  // By the key: a new object with the same content is no change.
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [key, ms]);
  return settled;
}
