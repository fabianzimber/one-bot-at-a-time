export const demoPrompts = [
  "Wie viele Urlaubstage hat emp-001?",
  "Wie hoch ist das Jahresgehalt von emp-014?",
  "Zeige mir das Organigramm der IT-Abteilung.",
  "Suche in den hochgeladenen Dokumenten nach der Homeoffice-Regelung und nenne die Quelle.",
  "Fasse die relevanteste Passage aus den hochgeladenen Dokumenten zur Urlaubsrichtlinie kurz zusammen.",
]

export function getRandomDemoPrompt() {
  return demoPrompts[Math.floor(Math.random() * demoPrompts.length)] ?? demoPrompts[0]
}
