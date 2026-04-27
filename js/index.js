/* =========================================================
   Utility Helpers
   ========================================================= */

const $ = (sel) => document.querySelector(sel);

function cleanPhotoPath(value) {
  return (value || "")
    .trim()
    .replace(/^assets\//i, "")
    .replace(/^photos\//i, "");
}

async function loadFeaturedHolesFromApi() {
  const response = await fetch("https://coursecaddy.onrender.com/api/holes");
  if (!response.ok) {
    throw new Error("Failed to load featured holes from API.");
  }
  return await response.json();
}

function shuffle(arr) {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function uniqueByCourse(rows) {
  const seen = new Set();
  const out = [];

  for (const row of rows) {
    const key = (row.Course || "").trim().toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }

  return out;
}

/* =========================================================
   Featured Signature Holes Rendering (Home Page)
   ========================================================= */

function renderFeatured(rows) {
  const container = $("#featured");
  const noPhotosMsg = $("#noPhotos");

  if (!container) return;

  container.innerHTML = "";
  noPhotosMsg.style.display = "none";

  const validPhotos = rows.filter((row) => {
    const cleaned = cleanPhotoPath(row.photo);
    const file = cleaned.split("/").pop()?.toLowerCase();
    return file && file !== "nophoto.png";
  });

  const picks = shuffle(uniqueByCourse(validPhotos)).slice(0, 3);

  if (!picks.length) {
    noPhotosMsg.style.display = "block";
    return;
  }

  picks.forEach((row) => {
    const imgSrc = "assets/photos/" + cleanPhotoPath(row.photo);

    const card = document.createElement("div");
    card.className = "hole-card";

    card.innerHTML = `
      <img class="hole-img"
           src="${imgSrc}"
           data-large="${imgSrc}"
           loading="lazy"
           alt="${row.Course || ""} – Hole ${row.Hole || ""}"
           onerror="this.src='assets/photos/nophoto.png'">
      <div class="hole-title">${row.Course || ""}</div>
      <div class="hole-sub">
        Hole ${row.Hole || ""}${row.par ? ` · Par ${row.par}` : ""}${row.yardage ? ` · ${row.yardage} yds` : ""}
      </div>
    `;

    card.querySelector(".hole-img").addEventListener("click", () => {
      $("#modalImg").src = imgSrc;
      $("#photoModal").classList.add("show");
      $("#photoModal").setAttribute("aria-hidden", "false");
    });

    container.appendChild(card);
  });
}

/* =========================================================
   Lightbox Modal Controls
   ========================================================= */

document.addEventListener("click", (event) => {
  const modal = $("#photoModal");

  if (!modal) return;

  if (
    event.target.classList.contains("modal-close") ||
    event.target === modal
  ) {
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
    $("#modalImg").src = "";
  }
});

document.addEventListener("keydown", (event) => {
  const modal = $("#photoModal");

  if (!modal) return;

  if (event.key === "Escape" && modal.classList.contains("show")) {
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
    $("#modalImg").src = "";
  }
});

/* =========================================================
   Back to Top Button
   ========================================================= */

document.addEventListener("click", (event) => {
  if (event.target.closest(".back-to-top")) {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
});

/* =========================================================
   Newsletter
   ========================================================= */

const newsletter = $("#newsletter");

if (newsletter) {
  newsletter.addEventListener("submit", (event) => {
    event.preventDefault();
    alert("Thanks for joining our newsletter!");
    newsletter.reset();
  });
}

/* =========================================================
   Initialize Home Page
   ========================================================= */

(async () => {
  try {
    const rows = await loadFeaturedHolesFromApi();
    renderFeatured(rows);
  } catch (error) {
    console.error("Home page API load error:", error);
    const noPhotosMsg = $("#noPhotos");
    if (noPhotosMsg) {
      noPhotosMsg.style.display = "block";
      noPhotosMsg.textContent = "Could not load featured holes from the API.";
    }
  }
})();
