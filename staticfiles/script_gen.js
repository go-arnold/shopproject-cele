// Canvas and particles - with null checks
const canvas = document.getElementById("particles");
const ctx = canvas ? canvas.getContext("2d") : null;
let particles = [];
let w, h;
let lastScroll = 0;

// DOM elements - safely query all elements
const tabbar = document.getElementById("mobileTabbar");
const searchBtn = document.getElementById("mobileSearchBtn");
const searchContainer = document.getElementById("mobileSearchContainer");

const priceRange = document.getElementById("priceRange");
const priceRangeValue = document.getElementById("priceRangeValue");
const applyFiltersBtn = document.getElementById("applyFilters");
const clearFiltersBtn = document.getElementById("clearFilters");
const productsGrid = document.getElementById("productsGrid");
const noResults = document.getElementById("noResults");

const sortSelect = document.getElementById("sort");

const messagesContainer = document.getElementById("messages-container");
const mobilePreviewBox = document.getElementById("mobilePreview");
const desktopPreviewBox = document.getElementById("desktopPreview");

const desktopInput = document.getElementById("desktopMessageInput");
const desktopSendBtn = document.getElementById("desktopSendBtn");
const desktopFileBtn = document.getElementById("desktopFileBtn");
const desktopFileInput = document.getElementById("desktopFileInput");

const mobileInput = document.getElementById("mobileMessageInput");
const mobileSendBtn = document.getElementById("mobileSendBtn");
const mobileFileBtn = document.getElementById("mobileFileBtn");
const mobileFileInput = document.getElementById("mobileFileInput");
let attachedFile = null;

const zoomModal = document.getElementById("imageZoomModal");
const zoomedImage = document.getElementById("zoomedImage");
const closeZoomBtn = document.getElementById("closeZoomBtn");

const mainImg = document.getElementById("mainImage");
const thumbs = document.querySelectorAll(".thumb");
const sizeBtns = document.querySelectorAll(".size-btn");

const qtyInput = document.getElementById("qtyInput");
const qtyPlus = document.getElementById("qtyPlus");
const qtyMinus = document.getElementById("qtyMinus");

// Canvas initialization - only if canvas exists
function init() {
  if (!canvas || !ctx) return;

  try {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.5 + 0.5,
      dx: (Math.random() - 0.5) * 0.2,
      dy: (Math.random() - 0.5) * 0.2,
    }));
  } catch (error) {
    console.error("Error initializing canvas:", error);
  }
}

function draw() {
  if (!canvas || !ctx || !particles.length) return;

  try {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "rgba(255,255,255,0.2)";
    particles.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > w) p.dx *= -1;
      if (p.y < 0 || p.y > h) p.dy *= -1;
    });
    requestAnimationFrame(draw);
  } catch (error) {
    console.error("Error in draw loop:", error);
  }
}

if (canvas && ctx) {
  window.addEventListener("resize", init);
  init();
  draw();
}

// Scroll handler - only if tabbar exists
if (tabbar) {
  window.addEventListener("scroll", () => {
    try {
      const curr = window.scrollY;
      if (curr > lastScroll && curr > 100) {
        tabbar.classList.add("hide");
      } else {
        tabbar.classList.remove("hide");
      }
      lastScroll = curr;
    } catch (error) {
      console.error("Error in scroll handler:", error);
    }
  });
}

// Intersection observer for fade-in elements
try {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) e.target.classList.add("visible");
    });
  });
  document.querySelectorAll(".fade-in").forEach((el) => observer.observe(el));
} catch (error) {
  console.error("Error setting up intersection observer:", error);
}

// Search button handler - only if elements exist
if (searchBtn && searchContainer) {
  searchBtn.addEventListener("click", (e) => {
    try {
      e.stopPropagation();
      searchContainer.classList.toggle("active");
      const input = searchContainer.querySelector("input");
      if (input && searchContainer.classList.contains("active")) {
        input.focus();
      }
    } catch (error) {
      console.error("Error in search button handler:", error);
    }
  });
}

// Click outside search handler
if (searchContainer && searchBtn) {
  document.addEventListener("click", (e) => {
    try {
      if (
        !searchContainer.contains(e.target) &&
        !searchBtn.contains(e.target)
      ) {
        searchContainer.classList.remove("active");
      }
    } catch (error) {
      console.error("Error in click outside handler:", error);
    }
  });
}

// Messages counter badge
document.addEventListener("DOMContentLoaded", () => {
  try {
    const badge = document.getElementById("messagesCounter");
    if (badge && typeof count !== "undefined") {
      if (count > 0) {
        badge.textContent = count;
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    }
  } catch (error) {
    console.error("Error updating messages counter:", error);
  }
});

// Favorite button handler
document.addEventListener("click", function (e) {
  if (!e.target.closest(".favorite-btn")) return;

  try {
    const btn = e.target.closest(".favorite-btn");
    const productId = btn.dataset.product;

    if (!productId) {
      console.warn("No product ID found");
      return;
    }

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) {
      console.error("CSRF token not found");
      return;
    }

    fetch(`/favori/${productId}/toggle/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken.value,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.favori) {
          btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
              <path d="m11.645 20.91-.007-.003-.022-.012a15.247 15.247 0 0 1-.383-.218 25.18 25.18 0 0 1-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0 1 12 5.052 5.5 5.5 0 0 1 16.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 0 1-4.244 3.17 15.247 15.247 0 0 1-.383.219l-.022.012-.007.004-.003.001a.752.752 0 0 1-.704 0l-.003-.001Z" />
            </svg>
          `;
        } else {
          btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
            </svg>
          `;
        }
      })
      .catch((err) => {
        console.error("Error toggling favorite:", err);
      });
  } catch (error) {
    console.error("Error in favorite button handler:", error);
  }
});

// Lazy background loading
document.addEventListener("DOMContentLoaded", () => {
  try {
    const lazyBgs = document.querySelectorAll(".lazy-bg");
    const lazyyBgs = document.querySelectorAll(".lazyy-bg");

    if (lazyBgs.length > 0 || lazyyBgs.length > 0) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const bg = el.getAttribute("data-bg");
            if (bg) {
              el.style.backgroundImage = `
                linear-gradient(0deg, rgba(18,18,28,0.7) 0%, rgba(18,18,28,0) 50%),
                url('${bg}')
              `;
              observer.unobserve(el);
            }
          }
        });
      });

      const observer_bien = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const bg = el.getAttribute("data-bg");
            if (bg) {
              el.style.backgroundImage = `url('${bg}')`;
              observer.unobserve(el);
            }
          }
        });
      });

      lazyBgs.forEach((bg) => observer.observe(bg));
      lazyyBgs.forEach((bg) => observer_bien.observe(bg));
    }
  } catch (error) {
    console.error("Error setting up lazy background loading:", error);
  }
});

// Cart count badge
document.addEventListener("DOMContentLoaded", () => {
  try {
    const badgee = document.getElementById("cart-count");
    const badge_one = document.getElementById("cart-count-one");

    if (typeof cart_count !== "undefined") {
      if (badgee) {
        if (cart_count > 0) {
          badgee.textContent = cart_count;
          badgee.classList.remove("hidden");
        } else {
          badgee.classList.add("hidden");
        }
      }

      if (badge_one) {
        if (cart_count > 0) {
          badge_one.textContent = cart_count;
          badge_one.classList.remove("hidden");
        } else {
          badge_one.classList.add("hidden");
        }
      }
    }
  } catch (error) {
    console.error("Error updating cart count:", error);
  }
});

// Message count badge
document.addEventListener("DOMContentLoaded", () => {
  try {
    const badg = document.getElementById("msg-count");

    if (badg && typeof countee !== "undefined") {
      if (countee > 0) {
        badg.textContent = countee;
        badg.classList.remove("hidden");
      } else {
        badg.classList.add("hidden");
      }
    }
  } catch (error) {
    console.error("Error updating message count:", error);
  }
});

// Price range filter
if (priceRange && priceRangeValue) {
  priceRange.addEventListener("input", (e) => {
    try {
      priceRangeValue.textContent = `${e.target.value}`;
    } catch (error) {
      console.error("Error updating price range value:", error);
    }
  });
}

if (applyFiltersBtn) {
  applyFiltersBtn.addEventListener("click", () => {
    try {
      if (priceRange) {
        const maxPrice = parseFloat(priceRange.value);
        filterProducts(maxPrice);
      }
    } catch (error) {
      console.error("Error applying filters:", error);
    }
  });
}

if (clearFiltersBtn && priceRange && priceRangeValue) {
  clearFiltersBtn.addEventListener("click", () => {
    try {
      priceRange.value = priceRange.max;
      priceRangeValue.textContent = `${priceRange.max}`;
      filterProducts(parseFloat(priceRange.max));
    } catch (error) {
      console.error("Error clearing filters:", error);
    }
  });
}

function filterProducts(maxPrice) {
  if (!productsGrid) return;

  try {
    const products = productsGrid.querySelectorAll("[data-price]");
    let visibleCount = 0;

    products.forEach((product) => {
      const price = parseFloat(product.dataset.price);
      if (!isNaN(price) && price <= maxPrice) {
        product.style.display = "";
        visibleCount++;
      } else {
        product.style.display = "none";
      }
    });

    if (noResults && productsGrid) {
      if (visibleCount === 0) {
        noResults.classList.remove("hidden");
        productsGrid.style.display = "none";
      } else {
        noResults.classList.add("hidden");
        productsGrid.style.display = "grid";
      }
    }
  } catch (error) {
    console.error("Error filtering products:", error);
  }
}

// Sort products
if (sortSelect) {
  sortSelect.addEventListener("change", (e) => {
    try {
      const sortValue = e.target.value;
      sortProducts(sortValue);
    } catch (error) {
      console.error("Error changing sort:", error);
    }
  });
}

function sortProducts(sortType) {
  if (!productsGrid) return;

  try {
    const products = Array.from(productsGrid.querySelectorAll("[data-price]"));

    products.sort((a, b) => {
      const priceA = parseFloat(a.dataset.price) || 0;
      const priceB = parseFloat(b.dataset.price) || 0;
      const reviewsA = parseInt(a.dataset.reviews) || 0;
      const reviewsB = parseInt(b.dataset.reviews) || 0;
      const dateA = a.dataset.date ? new Date(a.dataset.date) : new Date(0);
      const dateB = b.dataset.date ? new Date(b.dataset.date) : new Date(0);

      switch (sortType) {
        case "price-asc":
          return priceA - priceB;
        case "price-desc":
          return priceB - priceA;
        case "recent":
          return dateB - dateA;
        case "popular":
          return reviewsB - reviewsA;
        default:
          return 0;
      }
    });

    products.forEach((product) => {
      productsGrid.appendChild(product);
    });
  } catch (error) {
    console.error("Error sorting products:", error);
  }
}

// Alternative favorite handler with state management
document.addEventListener("click", function (e) {
  if (!e.target.closest(".favorite-btn")) return;

  try {
    const btn = e.target.closest(".favorite-btn");
    const productId = btn.dataset.product;

    if (!productId) return;

    if (btn.classList.contains("favori")) {
      btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
        </svg>
      `;
      btn.classList.remove("favori");
    } else {
      btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
          <path d="m11.645 20.91-.007-.003-.022-.012a15.247 15.247 0 0 1-.383-.218 25.18 25.18 0 0 1-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0 1 12 5.052 5.5 5.5 0 0 1 16.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 0 1-4.244 3.17 15.247 15.247 0 0 1-.383.219l-.022.012-.007.004-.003.001a.752.752 0 0 1-.704 0l-.003-.001Z" />
        </svg>
      `;
      btn.classList.add("favori");
    }

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrfToken) return;

    fetch(`/favori/${productId}/toggle/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken.value,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => res.json())
      .catch((err) => {
        console.error("Erreur lors de la requête:", err);
        // Revert UI on error
        if (btn.classList.contains("favori")) {
          btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
              <path d="m11.645 20.91-.007-.003-.022-.012a15.247 15.247 0 0 1-.383-.218 25.18 25.18 0 0 1-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0 1 12 5.052 5.5 5.5 0 0 1 16.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 0 1-4.244 3.17 15.247 15.247 0 0 1-.383.219l-.022.012-.007.004-.003.001a.752.752 0 0 1-.704 0l-.003-.001Z" />
            </svg>
          `;
        } else {
          btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z" />
            </svg>
          `;
        }
      });
  } catch (error) {
    console.error("Error in favorite toggle:", error);
  }
});

// Message functions - only if container exists
function scrollToBottom() {
  if (!messagesContainer) return;

  try {
    const container = messagesContainer.parentElement;
    if (container) {
      setTimeout(() => {
        container.scrollTop = container.scrollHeight + 500;
      }, 100);
    }
  } catch (error) {
    console.error("Error scrolling to bottom:", error);
  }
}

function renderMessage(msg, optimistic = false) {
  if (!messagesContainer || !msg) return;

  try {
    let tempId = null;
    if (optimistic) {
      tempId = `temp-${Date.now()}`;
    }

    const wrap = document.createElement("div");
    wrap.dataset.id = msg.id || tempId;
    wrap.className = `flex items-start gap-2 sm:gap-3 max-w-[90%] sm:max-w-2xl ${
      msg.is_me ? "self-end" : "self-start"
    } ${optimistic ? "optimistic-message" : ""}`;

    // Determine display name
    let displayName = msg.is_me ? "Vous" : msg.sender_name || "";
    if (!msg.is_me && typeof isRevendeur !== "undefined" && !isRevendeur) {
      displayName = "Agent Celebobo";
    }

    // Format timestamp
    const formattedTime =
      typeof formatLocalTime === "function"
        ? formatLocalTime(msg.timestamp)
        : msg.timestamp || "";

    let html = `
      <div class="${
        msg.is_me
          ? "order-1 flex flex-col items-end"
          : "order-2 flex flex-col items-start"
      }">
        <div class="flex items-baseline gap-1.5 sm:gap-2">
          <p class="text-xs sm:text-sm font-bold ${
            msg.is_me ? "text-white" : "text-slate-200"
          }">${displayName}</p>
          <span class="text-[0.65rem] sm:text-xs text-slate-400">${formattedTime}</span>
        </div>
    `;

    if (msg.image) {
      html += `<img src="${msg.image}" class="message-image mt-1 max-w-[200px] rounded-lg shadow-md" onclick="openImageZoom('${msg.image}')">`;
    }

    if (msg.content) {
      html += `
        <div class="mt-1 px-3 py-2 sm:px-4 sm:py-2 rounded-lg ${
          msg.is_me
            ? "rounded-br-none bg-primary/20 text-white"
            : "rounded-bl-none bg-slate-200 dark:bg-slate-700 text-white"
        }">
          <p class="leading-relaxed text-xs sm:text-sm">${msg.content}</p>
        </div>`;
    }

    html += "</div>";
    wrap.innerHTML = html;

    messagesContainer.appendChild(wrap);
    scrollToBottom();
  } catch (error) {
    console.error("Error rendering message:", error);
  }
}

function fetchMessages() {
  if (!messagesContainer || typeof messageApiUrl === "undefined") return;

  try {
    fetch(messageApiUrl)
      .then((r) => r.json())
      .then((json) => {
        if (json && json.messages && Array.isArray(json.messages)) {
          json.messages.forEach((msg) => {
            if (
              typeof lastMessageId !== "undefined" &&
              msg.id > lastMessageId
            ) {
              // Remove all optimistic messages
              document
                .querySelectorAll(`[data-id^="temp-"]`)
                .forEach((temp) => temp.remove());

              renderMessage(msg);
              lastMessageId = msg.id;
            }
          });
        }
      })
      .catch((err) => console.error("Erreur fetchMessages:", err));
  } catch (error) {
    console.error("Error in fetchMessages:", error);
  }
}

if (messagesContainer && typeof messageApiUrl !== "undefined") {
  setInterval(fetchMessages, 1000);
}

function sendMessage() {
  if (!messagesContainer) return;

  try {
    const text =
      (desktopInput ? desktopInput.value.trim() : "") ||
      (mobileInput ? mobileInput.value.trim() : "");
    const file = attachedFile;

    if (!text && !file) return;

    // Optimistic message with image AND text
    renderMessage(
      {
        id: null,
        is_me: true,
        content: text,
        image: file ? URL.createObjectURL(file) : null,
        timestamp: new Date().toISOString(),
      },
      true,
    );

    if (
      typeof csrfToken === "undefined" ||
      typeof postMessageUrl === "undefined"
    ) {
      console.error("Missing csrfToken or postMessageUrl");
      return;
    }

    const form = new FormData();
    form.append("csrfmiddlewaretoken", csrfToken);
    form.append("content", text);
    if (file) form.append("image", file);

    attachedFile = null;
    clearPreview();
    if (desktopInput) desktopInput.value = "";
    if (mobileInput) mobileInput.value = "";

    fetch(postMessageUrl, {
      method: "POST",
      body: form,
    })
      .then((response) => {
        if (!response.ok) throw new Error("Erreur serveur");
        return response.json();
      })
      .then(() => {
        // Immediate fetch after successful send
        setTimeout(fetchMessages, 300);
      })
      .catch((err) => {
        console.error("Erreur envoi:", err);
        document
          .querySelectorAll(`[data-id^="temp-"]`)
          .forEach((temp) => temp.remove());
        alert("Erreur lors de l'envoi du message. Veuillez réessayer.");
      });
  } catch (error) {
    console.error("Error in sendMessage:", error);
  }
}

if (desktopSendBtn) {
  desktopSendBtn.onclick = sendMessage;
}

if (mobileSendBtn) {
  mobileSendBtn.onclick = sendMessage;
}

if (desktopInput) {
  desktopInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}

if (mobileInput) {
  mobileInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}

function clearPreview() {
  try {
    if (mobilePreviewBox) {
      mobilePreviewBox.innerHTML = "";
      mobilePreviewBox.style.display = "none";
    }
    if (desktopPreviewBox) {
      desktopPreviewBox.innerHTML = "";
      desktopPreviewBox.style.display = "none";
    }
  } catch (error) {
    console.error("Error clearing preview:", error);
  }
}

function showPreview(file, isMobile) {
  if (!file) return;

  try {
    attachedFile = file;
    const url = URL.createObjectURL(file);
    const previewBox = isMobile ? mobilePreviewBox : desktopPreviewBox;

    if (!previewBox) return;

    previewBox.innerHTML = `
      <div class="flex items-center gap-3 p-2">
        <img src="${url}" class="max-w-[160px] max-h-[160px] rounded-lg shadow-md object-cover">
        <button id="cancelPreview" class="flex items-center justify-center bg-red-600 text-white rounded-full w-8 h-8 hover:bg-red-700 transition">
          <span class="material-symbols-outlined text-lg">close</span>
        </button>
      </div>
    `;
    previewBox.style.display = "block";

    const cancelBtn = document.getElementById("cancelPreview");
    if (cancelBtn) {
      cancelBtn.onclick = () => {
        attachedFile = null;
        clearPreview();
      };
    }
  } catch (error) {
    console.error("Error showing preview:", error);
  }
}

if (desktopFileBtn && desktopFileInput) {
  desktopFileBtn.onclick = () => desktopFileInput.click();
}

if (mobileFileBtn && mobileFileInput) {
  mobileFileBtn.onclick = () => mobileFileInput.click();
}

if (desktopFileInput) {
  desktopFileInput.onchange = () => {
    if (desktopFileInput.files && desktopFileInput.files[0]) {
      showPreview(desktopFileInput.files[0], false);
    }
  };
}

if (mobileFileInput) {
  mobileFileInput.onchange = () => {
    if (mobileFileInput.files && mobileFileInput.files[0]) {
      showPreview(mobileFileInput.files[0], true);
    }
  };
}

scrollToBottom();

// Image zoom functionality
window.openImageZoom = function (imageSrc) {
  if (!zoomModal || !zoomedImage || !imageSrc) return;

  try {
    zoomedImage.src = imageSrc;

    zoomModal.classList.remove("hidden");
    zoomModal.classList.add("flex");

    setTimeout(() => {
      zoomedImage.classList.remove("opacity-0", "scale-95");
      zoomedImage.classList.add("opacity-100", "scale-100");
    }, 20);

    document.body.style.overflow = "hidden";
  } catch (error) {
    console.error("Error opening image zoom:", error);
  }
};

function closeImageZoom() {
  if (!zoomModal || !zoomedImage) return;

  try {
    zoomedImage.classList.remove("opacity-100", "scale-100");
    zoomedImage.classList.add("opacity-0", "scale-95");

    setTimeout(() => {
      zoomModal.classList.add("hidden");
      zoomModal.classList.remove("flex");
      zoomedImage.src = "";
    }, 180);

    document.body.style.overflow = "";
  } catch (error) {
    console.error("Error closing image zoom:", error);
  }
}

if (closeZoomBtn) {
  closeZoomBtn.onclick = closeImageZoom;
}

if (zoomModal) {
  zoomModal.onclick = function (e) {
    if (e.target === zoomModal) {
      closeImageZoom();
    }
  };
}

document.addEventListener("keydown", function (e) {
  if (
    e.key === "Escape" &&
    zoomModal &&
    !zoomModal.classList.contains("hidden")
  ) {
    closeImageZoom();
  }
});

// Cookie helper
(function () {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      const modal = document.getElementById("conclureModal");
      if (!modal) return;

      const modalBody = document.getElementById("conclureModalBody");
      const closeModalBtn = modal.querySelector(".close-modal");
      let lastFocusedButton = null;

      function openLoader(triggerEl) {
        try {
          modal.setAttribute("aria-hidden", "false");
          modal.style.display = "flex";
          document.body.style.overflow = "hidden";

          if (modalBody) {
            modalBody.innerHTML = `
              <div style="text-align:center;padding:40px;">
                <div class="spinner"></div>
                <p style="margin-top:10px;color:#bbb;">Chargement…</p>
              </div>`;
          }

          if (triggerEl) {
            triggerEl.disabled = true;
            triggerEl.classList.add("loading");
          }
        } catch (error) {
          console.error("Error opening loader:", error);
        }
      }

      function closeModal() {
        try {
          modal.setAttribute("aria-hidden", "true");
          modal.style.display = "none";
          document.body.style.overflow = "";

          if (modalBody) {
            modalBody.innerHTML = "";
          }

          if (lastFocusedButton) {
            try {
              lastFocusedButton.blur();
            } catch (e) {
              /*ignore*/
            }
            lastFocusedButton.disabled = false;
            lastFocusedButton.classList.remove("loading");
            lastFocusedButton = null;
          }
        } catch (error) {
          console.error("Error closing modal:", error);
        }
      }

      modal.addEventListener("click", function (e) {
        if (e.target === modal) closeModal();
      });

      if (closeModalBtn) {
        closeModalBtn.addEventListener("click", closeModal);
      }

      document.querySelectorAll(".open-conclure-modal").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
          try {
            e.preventDefault();
            lastFocusedButton = btn;
            const url = btn.dataset.url;
            const pid = btn.dataset.conversationId || null;

            if (!url) {
              console.error("No URL found on button");
              return;
            }

            openLoader(btn);

            fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
              .then(function (res) {
                if (!res.ok) throw new Error("Bad response");
                return res.text();
              })
              .then(function (html) {
                if (modalBody) {
                  modalBody.innerHTML = html;

                  modalBody
                    .querySelectorAll(".close-modal-btn")
                    .forEach(function (cbtn) {
                      cbtn.addEventListener("click", function (ev) {
                        ev.preventDefault();
                        closeModal();
                      });
                    });

                  const form = modalBody.querySelector("form");
                  if (form) {
                    form.addEventListener("submit", function (ev) {
                      ev.preventDefault();
                      const csrftoken = getCookie("csrftoken");
                      const fd = new FormData(form);

                      if (!csrftoken) {
                        console.error("CSRF token not found");
                        return;
                      }

                      fetch(form.action, {
                        method: "POST",
                        headers: {
                          "X-Requested-With": "XMLHttpRequest",
                          "X-CSRFToken": csrftoken,
                        },
                        body: fd,
                        credentials: "same-origin",
                      })
                        .then(function (resp) {
                          return resp.json().catch(function () {
                            return { success: resp.ok };
                          });
                        })
                        .then(function (data) {
                          if (data && data.success) {
                            if (pid) {
                              window.location.href =
                                "{% url 'list_conversations' %}";
                              return;
                            }
                            window.location.reload();
                          } else {
                            console.error(
                              "Conclusion: réponse inattendue",
                              data,
                            );
                            window.location.reload();
                          }
                        })
                        .catch(function (err) {
                          console.error("Erreur lors du chargement:", err);
                          window.location.reload();
                        });
                    });
                  }
                }
              })
              .catch(function (err) {
                console.error("Erreur fetch modal:", err);
                if (modalBody) {
                  modalBody.innerHTML = `<div style="padding:40px;text-align:center;color:#aaa;">Erreur de chargement. <br><small>${err.message}</small></div>`;
                }
                if (btn) {
                  btn.disabled = false;
                  btn.classList.remove("loading");
                }
              });
          } catch (error) {
            console.error("Error in modal button handler:", error);
          }
        });
      });
    } catch (error) {
      console.error("Error setting up conclure modal:", error);
    }
  });
})();

// Conversation search
(function () {
  try {
    const input = document.getElementById("conversationSearch");
    const list = document.getElementById("conversationList");

    if (!input || !list) return;

    let timeout = null;

    input.addEventListener("input", function (e) {
      try {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          const q = input.value.trim();
          const url = new URL(window.location.href);
          url.searchParams.set("q", q);

          fetch(url.toString(), {
            headers: { "X-Requested-With": "XMLHttpRequest" },
          })
            .then((r) => r.text())
            .then((html) => {
              list.innerHTML = html;
            })
            .catch((err) => console.error(err));
        }, 350);
      } catch (error) {
        console.error("Error in conversation search:", error);
      }
    });
  } catch (error) {
    console.error("Error setting up conversation search:", error);
  }
})();

// Product image thumbnails
if (thumbs.length > 0 && mainImg) {
  thumbs.forEach((t) => {
    t.addEventListener("click", (e) => {
      try {
        const src = t.getAttribute("data-src");
        if (!src) return;

        mainImg.classList.remove("opacity-100");
        mainImg.style.opacity = 0;
        mainImg.style.transform = "scale(0.995)";

        setTimeout(() => {
          mainImg.src = src;

          thumbs.forEach((x) =>
            x.classList.remove("thumb-active", "border-primary"),
          );
          t.classList.add("thumb-active");

          mainImg.style.transform = "scale(1)";
          mainImg.style.opacity = 1;
        }, 180);
      } catch (error) {
        console.error("Error changing product image:", error);
      }
    });
  });
}

// Size selection buttons
if (sizeBtns.length > 0) {
  sizeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      try {
        if (btn.hasAttribute("disabled")) return;

        sizeBtns.forEach((b) => {
          b.classList.remove("ring-2", "ring-primary/60", "bg-primary");

          if (!b.hasAttribute("disabled")) {
            b.classList.add("bg-secondary-dark", "text-white");
          }
        });

        btn.classList.remove("bg-secondary-dark");
        btn.classList.add(
          "bg-primary",
          "text-white",
          "ring-2",
          "ring-primary/60",
          "size-btn-active",
        );

        // Store chosen size
        const parent = btn.closest("div");
        if (parent) {
          parent.dataset.selected = btn.textContent.trim();
        }
      } catch (error) {
        console.error("Error selecting size:", error);
      }
    });
  });
}

// Quantity input handlers
function sanitizeQty() {
  if (!qtyInput) return;

  try {
    let v = parseInt(qtyInput.value || "1", 10);
    if (isNaN(v) || v < 1) v = 1;
    qtyInput.value = v;
  } catch (error) {
    console.error("Error sanitizing quantity:", error);
  }
}

if (qtyPlus) {
  qtyPlus.addEventListener("click", () => {
    try {
      sanitizeQty();
      if (qtyInput) {
        qtyInput.value = parseInt(qtyInput.value, 10) + 1;
      }
    } catch (error) {
      console.error("Error incrementing quantity:", error);
    }
  });
}

if (qtyMinus) {
  qtyMinus.addEventListener("click", () => {
    try {
      sanitizeQty();
      if (qtyInput) {
        const val = Math.max(1, parseInt(qtyInput.value, 10) - 1);
        qtyInput.value = val;
      }
    } catch (error) {
      console.error("Error decrementing quantity:", error);
    }
  });
}

if (qtyInput) {
  qtyInput.addEventListener("input", () => {
    try {
      qtyInput.value = qtyInput.value.replace(/[^\d]/g, "");
    } catch (error) {
      console.error("Error filtering quantity input:", error);
    }
  });

  qtyInput.addEventListener("blur", sanitizeQty);
}

// Rating and testimonial form
(function () {
  try {
    const ratingBtns = document.querySelectorAll(".rating-btn");
    const ratingInput = document.getElementById("ratingInput");
    const ratingDisplay = document.getElementById("ratingDisplay");
    let ratingVal = parseInt(ratingInput?.value, 10) || 5;

    function updateStars(val) {
      try {
        ratingBtns.forEach((rb) => {
          const v = parseInt(rb.dataset.value, 10) || 0;
          rb.classList.toggle("text-primary", v <= val);
          rb.setAttribute("aria-checked", v === val ? "true" : "false");
        });

        if (ratingDisplay) {
          ratingDisplay.textContent = `${val} étoile${val > 1 ? "s" : ""}`;
        }

        if (ratingInput) {
          ratingInput.value = val;
        }
      } catch (error) {
        console.error("Error updating stars:", error);
      }
    }

    if (ratingBtns && ratingBtns.length) {
      updateStars(ratingVal);

      ratingBtns.forEach((b) => {
        b.addEventListener("click", () => {
          try {
            ratingVal = parseInt(b.dataset.value, 10) || 5;
            updateStars(ratingVal);
          } catch (error) {
            console.error("Error in rating click:", error);
          }
        });

        b.setAttribute("role", "radio");
        b.setAttribute("tabindex", "0");

        b.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            b.click();
          }
        });
      });
    }

    const testimonialForm = document.getElementById("testimonialForm");
    if (testimonialForm) {
      testimonialForm.addEventListener("submit", (e) => {
        try {
          if (ratingInput) {
            ratingInput.value = ratingVal;
          }

          const messageField =
            testimonialForm.querySelector('[name="message"]');
          const message = messageField?.value?.trim();

          if (!message) {
            e.preventDefault();
            alert("Merci de remplir votre message.");
            return;
          }

          if (typeof isAuthenticated !== "undefined" && !isAuthenticated) {
            e.preventDefault();
            window.location.href =
              "{% url 'account_login' %}?next={{ request.path }}";
            return;
          }
        } catch (error) {
          console.error("Error in testimonial form submit:", error);
          e.preventDefault();
        }
      });
    }
  } catch (error) {
    console.error("Error setting up rating system:", error);
  }
})();

// Accessibility enhancements for thumbnails
if (thumbs.length > 0) {
  thumbs.forEach((t) => {
    t.setAttribute("tabindex", "0");
    t.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        t.click();
      }
    });
  });
}

// Accessibility enhancements for size buttons
if (sizeBtns.length > 0) {
  sizeBtns.forEach((s) => {
    s.setAttribute("tabindex", "0");
    s.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        s.click();
      }
    });
  });
}
