// Presentation-only palette, indexed by the API's state order. No health judgment.
const colors = ["#536f8a", "#9c8259", "#b4a8c5", "#759ca6", "#79618c", "#b7bfc7", "#273e51"];
export const flowColor = (index: number) => colors[index % colors.length];
