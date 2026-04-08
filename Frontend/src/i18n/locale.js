export function getLocale(lang) {
  switch (lang) {
    case "ru":
      return "ru-RU";
    case "zh":
      return "zh-CN";
    case "en":
      return "en-US";
    default:
      return "en-US";
  }
}

