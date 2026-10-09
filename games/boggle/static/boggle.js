// Boggle board: count down, and let each player rotate the board or the
// tiles. Reloading for a new board is done by refresh.js.
const board = document.getElementById("boggle");
const timer = document.getElementById("timer");
let remaining = Number(timer.dataset.seconds);
let angle = 0;

setInterval(() => {
  remaining = Math.max(remaining - 1, 0);
  const seconds = String(remaining % 60).padStart(2, "0");
  timer.textContent = `${Math.floor(remaining / 60)}:${seconds}`;
}, 1000);

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
