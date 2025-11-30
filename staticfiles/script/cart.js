
document.addEventListener("DOMContentLoaded", () => {

    /* ---------------------------
    Helpers
    --------------------------- */
    function selectAll(selector, root = document) {
        return Array.from(root.querySelectorAll(selector));
    }

    function select(selector, root = document) {
        return root.querySelector(selector);
    }

    /* ---------------------------
    Update all cart counters (.cart-count)
    --------------------------- */
    function updateCartCounters(count) {
        selectAll(".cart-count").forEach(el => el.textContent = count);
    }

    /* ---------------------------
    Visual feedback: color inversion for a Tailwind-styled button
    (we assume original has bg-primary text-white)
    We'll temporarily add classes: bg-white text-primary ring (then revert)
    --------------------------- */
    function invertButtonVisual(btn) {
        if (!btn) return;
        // classes to add (Tailwind)
        const add = ["bg-white", "text-primary", "ring-2", "ring-primary"];
        const remove = ["bg-primary", "text-white"];
        btn.classList.remove(...remove);
        btn.classList.add(...add);
        setTimeout(() => {
            btn.classList.remove(...add);
            btn.classList.add(...remove);
        }, 220); // 220ms quick feedback
    }

    /* ---------------------------
    Small error toast (non blocking)
    --------------------------- */
    function showToast(message) {
        // Minimal unobtrusive toast
        const t = document.createElement("div");
        t.textContent = message;
        t.style.position = "fixed";
        t.style.right = "16px";
        t.style.bottom = "22px";
        t.style.zIndex = "9999";
        t.style.padding = "10px 14px";
        t.style.background = "rgba(0,0,0,0.85)";
        t.style.color = "#fff";
        t.style.borderRadius = "8px";
        t.style.fontSize = "13px";
        t.style.boxShadow = "0 6px 18px rgba(0,0,0,0.3)";
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 2500);
    }

    /* ====================================================
    Optimistic Add To Cart (instant UI, backend in background)
    Uses endpoint: /add-to-cart/
    Backend must accept product_id via POST.
    ==================================================== */
    function optimisticAddToCart(productId, btn) {
        try {
            // 1) Instant UI: increment counters immediately
            const currentCounts = selectAll(".cart-count").map(el => parseInt(el.textContent || "0", 10));
            const newCount = (currentCounts[0] || 0) + 1;
            updateCartCounters(newCount);

            // 2) Visual feedback instantly
            invertButtonVisual(btn);

            // 3) Send request in background (no UI dependency on response)
            const fd = new FormData();
            fd.append("product_id", productId);

            fetch("/add-to-cart/", {
                method: "POST",
                body: fd,
            })
                .then(res => res.json())
                .then(data => {
                    // we do NOT overwrite UI from server; only reconcile if server gives a count
                    if (data && typeof data.cart_count !== "undefined") {
                        updateCartCounters(data.cart_count);
                    }
                })
                .catch(err => {
                    // If error: revert one unit and notify
                    const fallbackCounts = selectAll(".cart-count").map(el => parseInt(el.textContent || "0", 10));
                    const reverted = Math.max((fallbackCounts[0] || 1) - 1, 0);
                    updateCartCounters(reverted);
                    console.error("add-to-cart failed", err);
                    showToast("Impossible d'ajouter au panier (réseau).");
                });
        } catch (e) {
            console.error(e);
        }
    }

    /* Attach to all add-to-cart buttons (site-wide) */
    selectAll(".add-to-cart-btn").forEach(btn => {
        btn.addEventListener("click", (ev) => {
            ev.preventDefault();
            const productId = btn.dataset.productId;
            optimisticAddToCart(productId, btn);
        });
    });

    /* ====================================================
    CART PAGE: optimistic quantity updates (+ / -) and delete
    Requirements in template:
        - each cart row has .cart-item and data-product-id="{{ item.product.id }}"
        - unit price element must have .item-unit-price and attribute data-unit-price="{{ item.price }}"
        - quantity input must have .item-qty (number)
        - per-row total must have .item-total-price (text like "123.45 $")
        - summary-subtotal id and summary-total id exist
    ==================================================== */

    // Utility: parse price string like "123.45 $" -> number
    function parsePrice(text) {
        if (!text) return 0;
        return parseFloat(text.toString().replace(/[^0-9.,-]/g, "").replace(",", ".") || 0);
    }

    // Recompute and update row total from unit price and qty (instant)
    function recomputeRowTotal(row, qty) {
        const unitEl = select(".item-unit-price", row);
        const unit = parseFloat(unitEl?.dataset?.unitPrice || unitEl?.textContent || 0) || 0;
        const newTotal = (unit * Number(qty));
        const totalEl = select(".item-total-price", row);
        if (totalEl) totalEl.textContent = newTotal.toFixed(2) + " $";
    }

    // Recompute summary (subtotal + total) instantly by summing row totals
    function recomputeSummary() {
        let subtotal = 0;
        selectAll(".cart-item").forEach(row => {
            const totalEl = select(".item-total-price", row);
            subtotal += parsePrice(totalEl?.textContent || "0");
        });
        const subtotalEl = document.getElementById("summary-subtotal");
        const totalEl = document.getElementById("summary-total");
        if (subtotalEl) subtotalEl.textContent = subtotal.toFixed(2) + " $";
        if (totalEl) totalEl.textContent = subtotal.toFixed(2) + " $";
    }

    // Send update to backend, but DON'T wait for it to update UI
    function sendUpdateQuantity(productId, qty, rollbackFn) {
        const fd = new FormData();
        fd.append("product_id", productId);
        fd.append("quantity", String(qty));

        fetch("/update-cart/", {
            method: "POST",
            body: fd,
        })
            .then(res => res.json())
            .then(data => {
                // If backend gives a definitive cart_count, sync counters silently
                if (data && typeof data.cart_count !== "undefined") {
                    updateCartCounters(data.cart_count);
                }
            })
            .catch(err => {
                console.error("update-cart failed", err);
                showToast("Impossible de mettre à jour le panier (réseau).");
                if (rollbackFn) rollbackFn();
            });
    }

    // Send remove request (background). rollbackFn re-inserts row if needed.
    function sendRemoveItem(productId, rollbackFn, successCallback) {
        const fd = new FormData();
        fd.append("product_id", productId);

        fetch("/remove-from-cart/", {
            method: "POST",
            body: fd,
        })
            .then(res => res.json())
            .then(data => {
                if (data && typeof data.cart_count !== "undefined") {
                    updateCartCounters(data.cart_count);
                }
                if (successCallback) successCallback();
            })
            .catch(err => {
                console.error("remove-from-cart failed", err);
                showToast("Impossible de supprimer l'élément (réseau).");
                if (rollbackFn) rollbackFn();
            });
    }

    /* CONNECT quantity buttons and delete on cart page */
    selectAll(".cart-item").forEach(row => {
        const productId = row.dataset.productId;
        const qtyInput = select(".item-qty", row);
        const decrease = select(".qty-btn.decrease", row);
        const increase = select(".qty-btn.increase", row);
        const deleteBtn = select(".delete-item", row);

        if (increase) {
            increase.addEventListener("click", (e) => {
                e.preventDefault();
                const oldQty = Number(qtyInput.value || 1);
                const newQty = oldQty + 1;
                // optimistic UI: update qty and row total immediately
                qtyInput.value = newQty;
                recomputeRowTotal(row, newQty);
                recomputeSummary();

                // send to backend, rollback on error
                sendUpdateQuantity(productId, newQty, () => {
                    // rollback
                    qtyInput.value = oldQty;
                    recomputeRowTotal(row, oldQty);
                    recomputeSummary();
                });
            });
        }

        if (decrease) {
            decrease.addEventListener("click", (e) => {
                e.preventDefault();
                const oldQty = Number(qtyInput.value || 1);
                if (oldQty <= 1) return; // do not go below 1
                const newQty = oldQty - 1;
                qtyInput.value = newQty;
                recomputeRowTotal(row, newQty);
                recomputeSummary();

                sendUpdateQuantity(productId, newQty, () => {
                    // rollback
                    qtyInput.value = oldQty;
                    recomputeRowTotal(row, oldQty);
                    recomputeSummary();
                });
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener("click", (e) => {
                e.preventDefault();
                // optimistic: remove row from DOM immediately but keep a backup to rollback
                const backup = row.cloneNode(true);
                const parent = row.parentNode;
                row.remove();
                recomputeSummary();

                // send remove request
                sendRemoveItem(productId,
                    // rollbackFn
                    () => {
                        // put row back in place
                        if (parent) parent.appendChild(backup);
                        recomputeSummary();
                    },
                    // successCallback (optional): nothing to do, row already removed
                    () => { }
                );
            });
        }
    });

    // Initial recompute (in case template server-rendered)
    recomputeSummary();

    // =====================  Tabbar overlay & loading  ==========================
    // Créer l'overlay de loading
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loadingOverlay';
    loadingOverlay.className = 'fixed inset-0 z-50 hidden';
    loadingOverlay.innerHTML = `
        <div class="fixed inset-0 flex items-center justify-center text-white overflow-hidden" style="background-color: rgba(10, 3, 20, 0.95);">
            <div class="absolute inset-0 z-0">
                <div class="absolute -top-1/4 -left-1/4 h-1/2 w-1/2 rounded-full bg-primary/20 blur-3xl opacity-50"></div>
                <div class="absolute -bottom-1/4 -right-1/4 h-1/2 w-1/2 rounded-full bg-primary/30 blur-3xl opacity-50"></div>
            </div>
            <div class="relative z-10 animate-pulse-glow">
                <img alt="CELEBOBO Logo"
                     class="w-32 h-auto"
                     src="/static/static-img/logo-white.png" />
            </div>
        </div>
    `;
    document.body.appendChild(loadingOverlay);

    // Ajouter l'animation pulse-glow au document
    if (!document.getElementById('pulseGlowStyle')) {
        const style = document.createElement('style');
        style.id = 'pulseGlowStyle';
        style.textContent = `
            @keyframes pulse-glow {
                0%, 100% {
                    filter: drop-shadow(0 0 5px #640D5F) drop-shadow(0 0 10px #640D5F);
                    opacity: 0.3;
                }
                50% {
                    filter: drop-shadow(0 0 15px #640D5F) drop-shadow(0 0 30px #640D5F);
                    opacity: 1;
                }
            }
            .animate-pulse-glow {
                animation: pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }
        `;
        document.head.appendChild(style);
    }

    // Variable pour suivre l'état de navigation
    let isNavigating = false;

    // Fonction pour afficher le loading
    function showLoading() {
        isNavigating = true;
        loadingOverlay.classList.remove('hidden');
    }

    // Fonction pour cacher le loading
    function hideLoading() {
        isNavigating = false;
        loadingOverlay.classList.add('hidden');
    }

    // Attacher l'événement à tous les liens du tabbar
    const tabbarLinks = document.querySelectorAll('#mobileTabbar a');
    tabbarLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            showLoading();
        });
    });

    // Cacher le loading quand la page est complètement chargée
    window.addEventListener('pageshow', function (event) {
        // Cacher le loading si on revient en arrière avec le bouton retour
        hideLoading();
    });

    // Gérer le bouton retour du navigateur
    window.addEventListener('popstate', function (event) {
        hideLoading();
    });

    // Cacher le loading si la navigation est annulée
    window.addEventListener('beforeunload', function () {
        if (!isNavigating) {
            hideLoading();
        }
    });

    // S'assurer que le loading est caché au chargement initial de la page
    hideLoading();

});