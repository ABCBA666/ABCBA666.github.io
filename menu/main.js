document.addEventListener("click", function (event) {
  var actionButton = event.target.closest(".bottom-action");
  if (!actionButton) {
    return;
  }
  var action = actionButton.getAttribute("data-action");
  console.log("Bottom action clicked:", action);
});
