/* =========================================================
   Quotes
   ========================================================= */

const golf_quotes = [
  { text: "The more I practice, the luckier I get.", author: "Gary Player" },
  { text: "Golf is a game of inches. The most important are the six inches between your ears.", author: "Arnold Palmer" },
  { text: "Success in golf depends less on strength of body than upon strength of mind and character.", author: "Arnold Palmer" },
  { text: "You swing your best when you have the fewest things to think about.", author: "Bobby Jones" },
  { text: "It’s a funny thing, the more I practice the luckier I get.", author: "Jerry Barber" },
  { text: "Resolve never to quit, never to give up, no matter what the situation.", author: "Jack Nicklaus" },
  { text: "Golf is deceptively simple and endlessly complicated.", author: "Harvey Penick" },
  { text: "A bad day of golf is better than a good day at work.", author: "Anonymous" },
  { text: "Putts get real difficult the day they hand out the money.", author: "Lee Trevino" },
  { text: "The most important shot in golf is the next one.", author: "Ben Hogan" },
  { text: "Competitive golf is played mainly on a five-inch course… the space between your ears.", author: "Bobby Jones" },
  { text: "Don’t be too proud to take lessons. I’m not.", author: "Jack Nicklaus" }];

let last_index = -1;


function get_random_index() {
  if (golf_quotes.length <= 1) return 0;
  let idx = Math.floor(Math.random() * golf_quotes.length);
  if (idx === last_index) {
    idx = (idx + 1) % golf_quotes.length;}
  last_index = idx;
  return idx;}


function render_quote() {
  const quote_text_el = document.getElementById("quote-text");
  const quote_author_el = document.getElementById("quote-author");
  if (!quote_text_el || !quote_author_el) return;

  const q = golf_quotes[get_random_index()];
  quote_text_el.textContent = q.text;
  quote_author_el.textContent = `— ${q.author}`;}


document.addEventListener("DOMContentLoaded", () => {
  // Initial quote on load
  render_quote();

  // Button: New Quote
  const btn = document.getElementById("new-quote-btn");
  if (btn) {
    btn.addEventListener("click", render_quote);
    // Keyboard support
    btn.addEventListener("keyup", (e) => {
      if (e.key === "Enter" || e.key === " ") render_quote(); });}});
