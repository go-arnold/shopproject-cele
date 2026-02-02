const canvas = document.getElementById("particles");
const ctx = canvas.getContext("2d");
let particles = [];
let w, h;
let lastScroll = 0;
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
//mobilePreviewBox.style.display = "none";
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

function init() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight;
  particles = Array.from({ length: 80 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() * 1.5 + 0.5,
    dx: (Math.random() - 0.5) * 0.2,
    dy: (Math.random() - 0.5) * 0.2,
  }));
}
function draw() {
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
}
window.addEventListener("resize", init);
init();
draw();

window.addEventListener("scroll", () => {
  const curr = window.scrollY;
  if (curr > lastScroll && curr > 100) tabbar.classList.add("hide");
  else tabbar.classList.remove("hide");
  lastScroll = curr;
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) e.target.classList.add("visible");
  });
});
document.querySelectorAll(".fade-in").forEach((el) => observer.observe(el));

searchBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  searchContainer.classList.toggle("active");
  const input = searchContainer.querySelector("input");
  if (searchContainer.classList.contains("active")) input.focus();
});

document.addEventListener("click", (e) => {
  if (!searchContainer.contains(e.target) && !searchBtn.contains(e.target)) {
    searchContainer.classList.remove("active");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const badge = document.getElementById("messagesCounter");
  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
});

document.addEventListener("click", function (e) {
  if (e.target.closest(".favorite-btn")) {
    const btn = e.target.closest(".favorite-btn");
    const productId = btn.dataset.product;

    fetch(`/favori/${productId}/toggle/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
          .value,
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
      });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const lazyBgs = document.querySelectorAll(".lazy-bg");
  const lazyyBgs = document.querySelectorAll(".lazyy-bg");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const bg = el.getAttribute("data-bg");
        el.style.backgroundImage = `
                            linear-gradient(0deg, rgba(18,18,28,0.7) 0%, rgba(18,18,28,0) 50%),
                            url('${bg}')
                        `;
        observer.unobserve(el);
      }
    });
  });

  const observer_bien = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const bg = el.getAttribute("data-bg");
        el.style.backgroundImage = `
                            url('${bg}')
                        `;
        observer.unobserve(el);
      }
    });
  });

  lazyBgs.forEach((bg) => observer.observe(bg));
  lazyyBgs.forEach((bg) => observer_bien.observe(bg));
});

document.addEventListener("DOMContentLoaded", () => {
  const badgee = document.getElementById("cart-count");
  const badge_one = document.getElementById("cart-count-one");

  if (cart_count > 0) {
    badgee.textContent = cart_count;
    badge_one.textContent = cart_count;
    badgee.classList.remove("hidden");
    badge_one.classList.remove("hidden");
  } else {
    badgee.classList.add("hidden");
    badge_one.classList.add("hidden");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const badg = document.getElementById("msg-count");

  if (countee > 0) {
    badg.textContent = countee;
    badg.classList.remove("hidden");
  } else {
    badg.classList.add("hidden");
  }
});

priceRange.addEventListener("input", (e) => {
  priceRangeValue.textContent = `${e.target.value}`;
});

applyFiltersBtn.addEventListener("click", () => {
  const maxPrice = parseFloat(priceRange.value);
  filterProducts(maxPrice);
});

clearFiltersBtn.addEventListener("click", () => {
  priceRange.value = priceRange.max;
  priceRangeValue.textContent = `${priceRange.max}`;
  filterProducts(parseFloat(priceRange.max));
});

function filterProducts(maxPrice) {
  const products = productsGrid.querySelectorAll("[data-price]");
  let visibleCount = 0;

  products.forEach((product) => {
    const price = parseFloat(product.dataset.price);
    if (price <= maxPrice) {
      product.style.display = "";
      visibleCount++;
    } else {
      product.style.display = "none";
    }
  });

  if (visibleCount === 0) {
    noResults.classList.remove("hidden");
    productsGrid.style.display = "none";
  } else {
    noResults.classList.add("hidden");
    productsGrid.style.display = "grid";
  }
}

sortSelect.addEventListener("change", (e) => {
  const sortValue = e.target.value;
  sortProducts(sortValue);
});

function sortProducts(sortType) {
  const products = Array.from(productsGrid.querySelectorAll("[data-price]"));

  products.sort((a, b) => {
    const priceA = parseFloat(a.dataset.price);
    const priceB = parseFloat(b.dataset.price);
    const reviewsA = parseInt(a.dataset.reviews) || 0;
    const reviewsB = parseInt(b.dataset.reviews) || 0;
    const dateA = new Date(a.dataset.date);
    const dateB = new Date(b.dataset.date);

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
}

document.addEventListener("click", function (e) {
  if (e.target.closest(".favorite-btn")) {
    const btn = e.target.closest(".favorite-btn");
    const productId = btn.dataset.product;

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

    fetch(`/favori/${productId}/toggle/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
          .value,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => res.json())
      .catch((err) => {
        console.error("Erreur lors de la requête:", err);
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
  }
});

function scrollToBottom() {
  const container = messagesContainer.parentElement;
  setTimeout(() => {
    container.scrollTop = container.scrollHeight + 500;
  }, 100);
}

function renderMessage(msg, optimistic = false) {
  let tempId = null;
  if (optimistic) {
    tempId = `temp-${Date.now()}`;
  }

  const wrap = document.createElement("div");
  wrap.dataset.id = msg.id || tempId;
  wrap.className = `flex items-start gap-2 sm:gap-3 max-w-[90%] sm:max-w-2xl ${
    msg.is_me ? "self-end" : "self-start"
  } ${optimistic ? "optimistic-message" : ""}`;

  // Déterminer le nom d'affichage
  let displayName = msg.is_me ? "Vous" : msg.sender_name || "";
  if (!msg.is_me && !isRevendeur) {
    displayName = "Agent Celebobo";
  }

  // Formater le timestamp
  const formattedTime = formatLocalTime(msg.timestamp);

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
                        <p class="leading-relaxed text-xs sm:text-sm">${
                          msg.content
                        }</p>
                    </div>`;
  }

  html += "</div>";
  wrap.innerHTML = html;

  messagesContainer.appendChild(wrap);
  scrollToBottom();
}

function fetchMessages() {
  fetch(messageApiUrl)
    .then((r) => r.json())
    .then((json) => {
      json.messages.forEach((msg) => {
        if (msg.id > lastMessageId) {
          // Supprimer TOUS les messages optimistes
          document
            .querySelectorAll(`[data-id^="temp-"]`)
            .forEach((temp) => temp.remove());

          renderMessage(msg);
          lastMessageId = msg.id;
        }
      });
    })
    .catch((err) => console.error("Erreur fetchMessages:", err));
}
setInterval(fetchMessages, 1000);

function sendMessage() {
  const text = desktopInput.value.trim() || mobileInput.value.trim();
  const file = attachedFile;

  if (!text && !file) return;

  // Message optimiste avec image ET texte
  renderMessage(
    {
      id: null,
      is_me: true,
      content: text,
      image: file ? URL.createObjectURL(file) : null,
      timestamp: new Date().toISOString(),
    },
    true
  );

  const form = new FormData();
  form.append("csrfmiddlewaretoken", csrfToken);
  form.append("content", text);
  if (file) form.append("image", file);

  attachedFile = null;
  clearPreview();
  desktopInput.value = "";
  mobileInput.value = "";

  fetch(postMessageUrl, {
    method: "POST",
    body: form,
  })
    .then((response) => {
      if (!response.ok) throw new Error("Erreur serveur");
      return response.json();
    })
    .then(() => {
      // Fetch immédiat après envoi réussi
      setTimeout(fetchMessages, 300);
    })
    .catch((err) => {
      console.error("Erreur envoi:", err);
      document
        .querySelectorAll(`[data-id^="temp-"]`)
        .forEach((temp) => temp.remove());
      alert("Erreur lors de l'envoi du message. Veuillez réessayer.");
    });
}
desktopSendBtn.onclick = sendMessage;
mobileSendBtn.onclick = sendMessage;
desktopInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
mobileInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

function clearPreview() {
  mobilePreviewBox.innerHTML = "";
  mobilePreviewBox.style.display = "none";
  desktopPreviewBox.innerHTML = "";
  desktopPreviewBox.style.display = "none";
}

function showPreview(file, isMobile) {
  attachedFile = file;
  const url = URL.createObjectURL(file);
  const previewBox = isMobile ? mobilePreviewBox : desktopPreviewBox;

  previewBox.innerHTML = `
                    <div class="flex items-center gap-3 p-2">
                        <img src="${url}" class="max-w-[160px] max-h-[160px] rounded-lg shadow-md object-cover">
                        <button id="cancelPreview" class="flex items-center justify-center bg-red-600 text-white rounded-full w-8 h-8 hover:bg-red-700 transition">
                            <span class="material-symbols-outlined text-lg">close</span>
                        </button>
                    </div>
                `;
  previewBox.style.display = "block";

  document.getElementById("cancelPreview").onclick = () => {
    attachedFile = null;
    clearPreview();
  };
}

desktopFileBtn.onclick = () => desktopFileInput.click();
mobileFileBtn.onclick = () => mobileFileInput.click();

desktopFileInput.onchange = () => {
  if (desktopFileInput.files[0]) showPreview(desktopFileInput.files[0], false);
};
mobileFileInput.onchange = () => {
  if (mobileFileInput.files[0]) showPreview(mobileFileInput.files[0], true);
};
scrollToBottom();

window.openImageZoom = function (imageSrc) {
  zoomedImage.src = imageSrc;

  zoomModal.classList.remove("hidden");
  zoomModal.classList.add("flex");

  setTimeout(() => {
    zoomedImage.classList.remove("opacity-0", "scale-95");
    zoomedImage.classList.add("opacity-100", "scale-100");
  }, 20);

  document.body.style.overflow = "hidden";
};

function closeImageZoom() {
  zoomedImage.classList.remove("opacity-100", "scale-100");
  zoomedImage.classList.add("opacity-0", "scale-95");

  setTimeout(() => {
    zoomModal.classList.add("hidden");
    zoomModal.classList.remove("flex");
    zoomedImage.src = "";
  }, 180);

  document.body.style.overflow = "";
}

closeZoomBtn.onclick = closeImageZoom;

zoomModal.onclick = function (e) {
  if (e.target === zoomModal) {
    closeImageZoom();
  }
};

document.addEventListener("keydown", function (e) {
  if (e.key === "Escape" && !zoomModal.classList.contains("hidden")) {
    closeImageZoom();
  }
});

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
    const modal = document.getElementById("conclureModal");
    if (!modal) return;
    const modalBody = document.getElementById("conclureModalBody");
    const closeModalBtn = modal.querySelector(".close-modal");
    let lastFocusedButton = null;

    function openLoader(triggerEl) {
      modal.setAttribute("aria-hidden", "false");
      modal.style.display = "flex";
      document.body.style.overflow = "hidden";
      modalBody.innerHTML = `
                        <div style="text-align:center;padding:40px;">
                            <div class="spinner"></div>
                            <p style="margin-top:10px;color:#bbb;">Chargement…</p>
                        </div>`;
      if (triggerEl) {
        triggerEl.disabled = true;
        triggerEl.classList.add("loading");
      }
    }

    function closeModal() {
      modal.setAttribute("aria-hidden", "true");
      modal.style.display = "none";
      document.body.style.overflow = "";
      modalBody.innerHTML = "";
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
    }

    modal.addEventListener("click", function (e) {
      if (e.target === modal) closeModal();
    });

    if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);

    document.querySelectorAll(".open-conclure-modal").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        lastFocusedButton = btn;
        const url = btn.dataset.url;
        const pid = btn.dataset.conversationId || null;

        openLoader(btn);

        fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then(function (res) {
            if (!res.ok) throw new Error("Bad response");
            return res.text();
          })
          .then(function (html) {
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
                        window.location.href = "{% url 'list_conversations' %}";
                        return;
                      }

                      window.location.reload();
                    } else {
                      console.error("Conclusion: réponse inattendue", data);
                      window.location.reload();
                    }
                  })
                  .catch(function (err) {
                    console.error("Erreur lors du chargement:", err);
                    window.location.reload();
                  });
              });
            }
          })
          .catch(function (err) {
            console.error("Erreur fetch modal:", err);
            modalBody.innerHTML = `<div style="padding:40px;text-align:center;color:#aaa;">Erreur de chargement. <br><small>${err.message}</small></div>`;
            if (btn) {
              btn.disabled = false;
              btn.classList.remove("loading");
            }
          });
      });
    });
  });
})();

(function () {
  const input = document.getElementById("conversationSearch");
  const list = document.getElementById("conversationList");
  let timeout = null;
  input.addEventListener("input", function (e) {
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
  });
})();

thumbs.forEach((t) => {
  t.addEventListener("click", (e) => {
    const src = t.getAttribute("data-src");
    if (!src) return;

    mainImg.classList.remove("opacity-100");
    mainImg.style.opacity = 0;

    mainImg.style.transform = "scale(0.995)";
    setTimeout(() => {
      mainImg.src = src;

      thumbs.forEach((x) =>
        x.classList.remove("thumb-active", "border-primary")
      );
      t.classList.add("thumb-active");

      mainImg.style.transform = "scale(1)";
      mainImg.style.opacity = 1;
    }, 180);
  });
});

sizeBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.hasAttribute("disabled")) return;
    sizeBtns.forEach((b) => {
      b.classList.remove("ring-2", "ring-primary/60", "bg-primary");

      if (!b.hasAttribute("disabled"))
        b.classList.add("bg-secondary-dark", "text-white");
    });

    btn.classList.remove("bg-secondary-dark");
    btn.classList.add(
      "bg-primary",
      "text-white",
      "ring-2",
      "ring-primary/60",
      "size-btn-active"
    );
    // optional: store chosen size in dataset for cart
    btn.closest("div").dataset.selected = btn.textContent.trim();
  });
});

function sanitizeQty() {
  let v = parseInt(qtyInput.value || "1", 10);
  if (isNaN(v) || v < 1) v = 1;
  qtyInput.value = v;
}
qtyPlus.addEventListener("click", () => {
  sanitizeQty();
  qtyInput.value = parseInt(qtyInput.value, 10) + 1;
});
qtyMinus.addEventListener("click", () => {
  sanitizeQty();
  const val = Math.max(1, parseInt(qtyInput.value, 10) - 1);
  qtyInput.value = val;
});
qtyInput.addEventListener("input", () => {
  // allow only numbers
  qtyInput.value = qtyInput.value.replace(/[^\d]/g, "");
});
qtyInput.addEventListener("blur", sanitizeQty);

(function () {
  const ratingBtns = document.querySelectorAll(".rating-btn");
  const ratingInput = document.getElementById("ratingInput");
  const ratingDisplay = document.getElementById("ratingDisplay");
  let ratingVal = parseInt(ratingInput?.value, 10) || 5;

  function updateStars(val) {
    ratingBtns.forEach((rb) => {
      const v = parseInt(rb.dataset.value, 10) || 0;
      rb.classList.toggle("text-primary", v <= val);
      rb.setAttribute("aria-checked", v === val ? "true" : "false");
    });
    if (ratingDisplay)
      ratingDisplay.textContent = `${val} étoile${val > 1 ? "s" : ""}`;
    if (ratingInput) ratingInput.value = val;
  }

  if (ratingBtns && ratingBtns.length) {
    updateStars(ratingVal);
    ratingBtns.forEach((b) => {
      b.addEventListener("click", () => {
        ratingVal = parseInt(b.dataset.value, 10) || 5;
        updateStars(ratingVal);
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
      if (ratingInput) ratingInput.value = ratingVal;

      const message = testimonialForm
        .querySelector('[name="message"]')
        ?.value?.trim();
      if (!message) {
        e.preventDefault();
        alert("Merci de remplir votre message.");
        return;
      }
      if (!isAuthenticated) {
        e.preventDefault();
        window.location.href =
          "{% url 'account_login' %}?next={{ request.path }}";
        return;
      }
      // allow normal POST
    });
  }
})();

thumbs.forEach((t) => {
  t.setAttribute("tabindex", "0");
  t.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") t.click();
  });
});
sizeBtns.forEach((s) => {
  s.setAttribute("tabindex", "0");
  s.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") s.click();
  });
});
