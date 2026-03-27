export const demoPrompts = [
  "Wie viele Urlaubstage hat Frau Dowerg noch?",
  "Was verdient Rosalie brutto im Jahr?",
  "Zeig mir bitte die Zeiterfassung von Andrei.",
  "Zeige mir das Organigramm der IT-Abteilung.",
  "Suche in den hochgeladenen Dokumenten nach der Homeoffice-Regelung und nenne die Quelle.",
  "Fasse die relevanteste Passage aus den hochgeladenen Dokumenten zur Urlaubsrichtlinie kurz zusammen.",
]

export function getRandomDemoPrompt() {
  return demoPrompts[Math.floor(Math.random() * demoPrompts.length)] ?? demoPrompts[0]
}
