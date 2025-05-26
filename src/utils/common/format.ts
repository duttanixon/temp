// src/lib/utils/format.ts
/**
 * Formats a number into a compact SI representation (e.g., 1000 -> 1K, 1500000 -> 1.5M).
 * @param number The number to format.
 * @param minToFormat The minimum number to apply SI formatting (defaults to 1000).
 * @param fractionDigits The number of fraction digits for SI formatted numbers (defaults to 1).
 * @returns The formatted string.
 */
export function formatCompactSI(
  number: number,
  minToFormat = 1000,
  fractionDigits = 1
): string {
  if (number === undefined || number === null) return "N/A";
  if (Math.abs(number) < minToFormat) {
    return number.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  const si = [
    { value: 1, symbol: "" },
    { value: 1e3, symbol: "K" },
    { value: 1e6, symbol: "M" },
    { value: 1e9, symbol: "G" },
    { value: 1e12, symbol: "T" },
    { value: 1e15, symbol: "P" },
    { value: 1e18, symbol: "E" },
  ];
  const rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
  let i;
  for (i = si.length - 1; i > 0; i--) {
    if (Math.abs(number) >= si[i].value) {
      break;
    }
  }
  return (
    (number / si[i].value).toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: fractionDigits,
    }) + si[i].symbol
  );
}
