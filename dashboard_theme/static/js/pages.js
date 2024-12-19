document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("data-table");

  // Move a row up
  const moveRowUp = (row) => {
    const prevRow = row.previousElementSibling;
    if (prevRow && prevRow.nodeName === "TR") {
      row.parentNode.insertBefore(row, prevRow);
      updateOrder();
    }
  };

  // Move a row down
  const moveRowDown = (row) => {
    const nextRow = row.nextElementSibling;
    if (nextRow && nextRow.nodeName === "TR") {
      row.parentNode.insertBefore(nextRow, row);
      updateOrder();
    }
  };

  // Update the order column
  const updateOrder = () => {
    const rows = table.querySelectorAll("tbody tr");
    rows.forEach((row, index) => {
      const orderCell = row.querySelector("td:first-child");
      orderCell.textContent = index + 1;
    });
  };

  // Event delegation for buttons
  table.addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;

    const row = target.closest("tr");
    if (target.id === "button-up") {
      moveRowUp(row);
    } else if (target.id === "button-down") {
      moveRowDown(row);
    }
  });
});

function saveData(csrfToken, redirectUrl) {
  const table = document.getElementById("data-table");
  const rows = table.querySelectorAll("tbody tr");
  const orderData = Array.from(rows).map((row) => {
    const pageId = row.querySelector("td:nth-child(2)").textContent.trim();
    const order = row.querySelector("td:first-child").textContent.trim();
    return { page_id: pageId, order: parseInt(order, 10) };
  });

  fetch(window.location.href, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken, // Token CSRF w nagłówku
    },
    body: JSON.stringify({ order: orderData }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Error during saving order");
      }
      return response.json();
    })
    .then(() => {
      // Po zapisaniu przekieruj na 'show_pages'
      window.location.href = redirectUrl;
    })
    .catch((error) => {
      console.error("Error saving order:", error);
      alert("Wystąpił błąd podczas zapisywania kolejności.");
    });
}
