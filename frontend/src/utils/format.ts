const shekel = new Intl.NumberFormat('en-IL', { style: 'currency', currency: 'ILS', minimumFractionDigits: 2 });

/** "12.4" or 12.4 -> "₪12.40". Money stays a decimal string until display. */
export function formatPrice(value: string | number): string {
  return shekel.format(typeof value === 'string' ? Number(value) : value);
}

/** 2 -> "2 ×", 0.5 kg -> "0.5 kg" */
export function formatQuantity(quantity: number, unit: 'unit' | 'kg'): string {
  const n = Number.isInteger(quantity) ? String(quantity) : quantity.toFixed(2).replace(/0+$/, '');
  return unit === 'kg' ? `${n} kg` : `${n} ×`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}
