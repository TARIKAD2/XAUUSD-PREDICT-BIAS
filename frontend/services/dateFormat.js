function parseDate(value) {
  if (value == null || value === "") return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value, options = {}) {
  const date = parseDate(value);
  if (!date) return value == null || value === "" ? "—" : String(value);

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...options,
  }).format(date);
}

export function formatDateTime(value, options = {}) {
  return formatDate(value, {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    ...options,
  });
}