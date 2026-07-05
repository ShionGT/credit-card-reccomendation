/**
 * Card listing page - filter & sort logic
 */

function filterCards() {
    const tagFilter = document.getElementById("filterTag").value;
    const feeFilter = document.getElementById("filterFee").value;
    const sortBy = document.getElementById("sortBy").value;

    const cards = document.querySelectorAll(".card-mini");
    let visibleCount = 0;

    cards.forEach(card => {
        let visible = true;

        // Tag filter
        if (tagFilter) {
            const tags = (card.dataset.tags || "").split(",");
            if (!tags.includes(tagFilter)) visible = false;
        }

        // Fee filter
        if (feeFilter === "free") {
            if (card.dataset.fee !== "0") visible = false;
        } else if (feeFilter === "paid") {
            if (card.dataset.fee === "0") visible = false;
        }

        card.style.display = visible ? "" : "none";
        if (visible) visibleCount++;
    });

    // Sort
    const grid = document.getElementById("cardGrid");
    const visibleCards = Array.from(grid.children).filter(c => c.style.display !== "none");

    visibleCards.sort((a, b) => {
        switch(sortBy) {
            case "name":
                return a.dataset.name.localeCompare(b.dataset.name);
            case "fee_low":
                return parseFloat(a.dataset.fee) - parseFloat(b.dataset.fee);
            case "cashback":
                return parseFloat(b.dataset.cashback) - parseFloat(a.dataset.cashback);
            case "rating":
            default:
                return parseFloat(b.dataset.rating) - parseFloat(a.dataset.rating);
        }
    });

    visibleCards.forEach(c => grid.appendChild(c));
}

// Populate tag filter on load
document.addEventListener("DOMContentLoaded", function() {
    const allTags = new Set();
    document.querySelectorAll(".card-mini").forEach(card => {
        const tags = (card.dataset.tags || "").split(",");
        tags.forEach(t => { if (t) allTags.add(t); });
    });

    const select = document.getElementById("filterTag");
    Array.from(allTags).sort().forEach(tag => {
        const opt = document.createElement("option");
        opt.value = tag;
        opt.textContent = tag;
        select.appendChild(opt);
    });
});
