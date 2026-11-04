export function shuffleOptions(options, random = Math.random) {
  const shuffled = (options || []).map((option, index) => ({
    ...option,
    number: option.number ?? index + 1,
  }))
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}
