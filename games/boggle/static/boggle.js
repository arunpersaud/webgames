// Boggle board: count down, reload when someone starts a new board, and
// let each player rotate the board or the tiles.
const board = document.getElementById("boggle");
const timer = document.getElementById("timer");
let remaining = Number(timer.dataset.seconds);
let angle = 0;

async function tick() {
  remaining = Math.max(remaining - 1, 0);
  const seconds = String(remaining % 60).padStart(2, "0");
  timer.textContent = `${Math.floor(remaining / 60)}:${seconds}`;

  try {
    const response = await fetch(board.dataset.update, { cache: "no-store" });
    const data = await response.json();
    if (data.started > Number(board.dataset.started)) {
      location.reload();
    }
  } catch {
    // network hiccup: try again on the next tick
  }
}

setInterval(tick, 1000);

for (const button of document.querySelectorAll("[data-rotate]")) {
  button.addEventListener("click", () => {
    angle += 90 * Number(button.dataset.rotate);
    board.style.transform = `rotate(${angle}deg)`;
  });
}

document.getElementById("rotate-tiles").addEventListener("click", () => {
  for (const tile of board.querySelectorAll("img")) {
    tile.style.transform = `rotate(${90 * Math.floor(Math.random() * 4)}deg)`;
  }
});
