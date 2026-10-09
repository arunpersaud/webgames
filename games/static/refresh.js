// Reload the page when the game changes on the server.
// Opt in with an element carrying
//   data-poll="<url>"   JSON endpoint returning {"version": ...}
//   data-version="..."  the version this page was rendered with
//   data-poll-interval  optional, in ms (default 3000)
const watched = document.querySelector("[data-poll]");

if (watched) {
  setInterval(async () => {
    try {
      const response = await fetch(watched.dataset.poll, { cache: "no-store" });
      const data = await response.json();
      if (String(data.version) !== watched.dataset.version) {
        location.reload();
      }
    } catch {
      // network hiccup: try again next time
    }
  }, Number(watched.dataset.pollInterval || 3000));
}
