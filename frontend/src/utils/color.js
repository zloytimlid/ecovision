/** Dark or white text, whichever is readable on the given HEX background. */
export function textColorOn(hex) {
  const value = (hex || '#000000').replace('#', '')
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16) / 255)
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
  return luminance > 0.55 ? '#1f2937' : '#ffffff'
}
