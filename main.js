document.addEventListener("click", function (event) {
  var actionButton = event.target.closest(".bottom-action");
  if (!actionButton) {
    return;
  }
  var action = actionButton.getAttribute("data-action");
  console.log("Bottom action clicked:", action);
});

document.addEventListener("DOMContentLoaded", function () {
  var batchPage = document.querySelector(".batch-page");
  if (!batchPage) {
    return;
  }
  var select = document.querySelector(".batch-select");
  if (!select) {
    return;
  }

  fetch("http://127.0.0.1:8000/api/departments")
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Failed to load departments");
      }
      return response.json();
    })
    .then(function (data) {
      if (!data || !Array.isArray(data.items)) {
        return;
      }
      while (select.options.length > 1) {
        select.remove(1);
      }
      data.items.forEach(function (item) {
        var option = document.createElement("option");
        option.value = String(item.id);
        option.textContent = item.name;
        select.appendChild(option);
      });
    })
    .catch(function (error) {
      console.error(error);
    });

  var uploadButton = document.getElementById("btn-upload");
  var fileInput = document.getElementById("file-input");
  var tableBody = document.getElementById("file-table-body");
  var validateButton = document.querySelector(".btn-secondary");

  var selectedFiles = [];

  if (uploadButton && fileInput && tableBody) {
    uploadButton.addEventListener("click", function () {
      fileInput.click();
    });

    fileInput.addEventListener("change", function () {
      selectedFiles = Array.from(fileInput.files || []);
      renderFileTable();
    });
  }

  function renderFileTable() {
    while (tableBody.firstChild) {
      tableBody.removeChild(tableBody.firstChild);
    }

    if (!selectedFiles || selectedFiles.length === 0) {
      var emptyRow = document.createElement("tr");
      emptyRow.className = "batch-empty-row";
      var emptyCell = document.createElement("td");
      emptyCell.colSpan = 4;
      emptyCell.className = "batch-empty-cell";
      emptyCell.textContent = "点击上方“点击上传”按钮";
      emptyRow.appendChild(emptyCell);
      tableBody.appendChild(emptyRow);
      if (validateButton) {
        validateButton.disabled = true;
      }
      return;
    }

    selectedFiles.forEach(function (file, index) {
      var tr = document.createElement("tr");

      var nameTd = document.createElement("td");
      nameTd.textContent = file.name;
      tr.appendChild(nameTd);

      var sizeTd = document.createElement("td");
      sizeTd.textContent = (file.size / 1024).toFixed(1) + " KB";
      tr.appendChild(sizeTd);

      var statusTd = document.createElement("td");
      statusTd.textContent = "待校验";
      statusTd.dataset.statusCell = "true";
      tr.appendChild(statusTd);

      var actionTd = document.createElement("td");
      var delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.textContent = "删除";
      delBtn.className = "btn-link";
      delBtn.addEventListener("click", function () {
        selectedFiles.splice(index, 1);
        renderFileTable();
      });
      actionTd.appendChild(delBtn);
      tr.appendChild(actionTd);

      tableBody.appendChild(tr);
    });

    if (validateButton) {
      validateButton.disabled = selectedFiles.length === 0;
    }
  }

  if (validateButton) {
    validateButton.addEventListener("click", function () {
      if (!selectedFiles || selectedFiles.length === 0 || validateButton.disabled) {
        return;
      }

      var formData = new FormData();
      selectedFiles.forEach(function (file) {
        formData.append("files", file, file.name);
      });

      validateButton.disabled = true;
      fetch("http://127.0.0.1:8000/api/batch-upload", {
        method: "POST",
        body: formData,
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("上传失败");
          }
          return response.json();
        })
        .then(function (data) {
          var results = (data && Array.isArray(data.results)) ? data.results : [];
          var rows = tableBody.querySelectorAll("tr");
          rows.forEach(function (row) {
            var nameCell = row.cells && row.cells[0];
            var statusCell = row.cells && row.cells[2];
            if (!nameCell || !statusCell) {
              return;
            }
            var filename = nameCell.textContent || "";
            var match = results.find(function (r) { return r.filename === filename; });
            if (!match) {
              return;
            }
            statusCell.textContent = match.status === "ok" ? "校验通过" : match.reason || "校验失败";
          });
        })
        .catch(function (error) {
          console.error(error);
          alert("上传或校验失败，请稍后再试");
        })
        .finally(function () {
          if (validateButton) {
            validateButton.disabled = selectedFiles.length === 0;
          }
        });
    });
  }
});
