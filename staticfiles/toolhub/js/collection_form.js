// JS for Collection Form
function setupVisibilityToggle() {
    const visBtn = document.getElementById("visibility-toggle");
    const visHidden = document.querySelector('input[name="visibility"]');
    const usersCard = document.getElementById("users-card");
  
    if (visBtn && visHidden) {
      visBtn.addEventListener("click", () => {
        const isPublic = visBtn.dataset.visibility === "public";
        visBtn.dataset.visibility = isPublic ? "private" : "public";
        visHidden.value = visBtn.dataset.visibility;
        visBtn.innerHTML = isPublic
          ? '<i class="bi bi-lock-fill text-danger"></i> Private'
          : '<i class="bi bi-globe text-success"></i> Public';
        if (usersCard) usersCard.style.display = isPublic ? "block" : "none";
      });
    }
  }
  
  function setupImagePreview() {
    const imgUpload = document.getElementById("image-upload");
    const preview = document.getElementById("image-preview");
    if (imgUpload && preview) {
      imgUpload.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) {
          preview.innerHTML = '<img src="/static/toolhub/images/default_collection.png" class="img-fluid rounded" style="max-height: 200px;">';
          return;
        }
        const reader = new FileReader();
        reader.onload = (ev) => {
          preview.innerHTML = `<img src="${ev.target.result}" class="img-fluid rounded" style="max-height: 200px;">`;
        };
        reader.readAsDataURL(file);
      });
    }
  }
  
  function removeHiddenInput(id, name) {
    const inputs = document.querySelectorAll(`input[name="${name}"][value="${id}"]`);
    inputs.forEach(el => el.remove());
  }
  
  function removeUser(userId) {
    const inputs = document.querySelectorAll(`input[name="allowed_users"][value="${userId}"]`);
    inputs.forEach(el => el.remove());
  
    const row = document.querySelector(`#preview-users tr[data-user-id="${userId}"]`);
    if (row) row.remove();
  }  
  
  function removeItem(itemId) {
    // Remove hidden input
    const inputs = document.querySelectorAll(`input[name="items"][value="${itemId}"]`);
    inputs.forEach(el => el.remove());
  
    // Remove table row
    const row = document.querySelector(`#selected-items tr[data-item-id="${itemId}"]`);
    if (row) row.remove();
  }
  
  function addItemRow(item) {
    const table = document.getElementById("selected-items");
    if (document.querySelector(`#selected-items tr[data-item-id="${item.id}"]`)) return;
    const row = document.createElement("tr");
    row.setAttribute("data-item-id", item.id);
    row.innerHTML = `
      <td>${table.children.length + 1}</td>
      <td>${item.title}</td>
      <td><span class="badge ${item.status === 'available' ? 'bg-success' : 'bg-secondary'}">${item.status_display}</span></td>
      <td>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeItem('${item.id}')">
          <i class="bi bi-x-circle"></i>
        </button>
        <input type="hidden" name="items" value="${item.id}">
      </td>`;
    table.appendChild(row);
  }
  
  function addUserRow(user) {
    const table = document.getElementById("preview-users");
    if (document.querySelector(`#preview-users tr[data-user-id="${user.id}"]`)) return;
    const row = document.createElement("tr");
    row.setAttribute("data-user-id", user.id);
    row.innerHTML = `
      <td>${table.children.length + 1}</td>
      <td>${user.name}</td>
      <td>${user.email}</td>
      <td>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeUser('${user.id}')">
          <i class="bi bi-x-circle"></i>
        </button>
        <input type="hidden" name="allowed_users" value="${user.id}">
      </td>`;
    table.appendChild(row);
  }
  
  function setupItemSearch() {
    const input = document.getElementById("item-search");
    if (input) {
      input.addEventListener("input", function () {
        const query = this.value.trim();
        const results = document.getElementById("item-search-results");
        if (query.length < 2) return results.innerHTML = "";
        fetch(`/api/search-items/?q=${encodeURIComponent(query)}`)
          .then(response => response.json())
          .then(data => {
            results.innerHTML = "";
            data.forEach(item => {
              const btn = document.createElement("button");
              btn.type = "button";
              btn.className = "list-group-item list-group-item-action";
              btn.textContent = item.title;
              btn.onclick = () => {
                addItemRow(item);
                results.innerHTML = "";
                input.value = "";
              };
              results.appendChild(btn);
            });
          });
      });
    }
  }
  
  function setupUserSearch() {
    const input = document.getElementById("user-search");
    if (input) {
      input.addEventListener("input", function () {
        const query = this.value.trim();
        const results = document.getElementById("user-search-results");
        if (query.length < 2) return results.innerHTML = "";
        fetch(`/api/search-users/?q=${encodeURIComponent(query)}`)
          .then(response => response.json())
          .then(data => {
            results.innerHTML = "";
            data.forEach(user => {
              const btn = document.createElement("button");
              btn.type = "button";
              btn.className = "list-group-item list-group-item-action";
              btn.textContent = `${user.name} (${user.email})`;
              btn.onclick = () => {
                addUserRow(user);
                results.innerHTML = "";
                input.value = "";
              };
              results.appendChild(btn);
            });
          });
      });
    }
  }
  
  document.addEventListener("DOMContentLoaded", function () {
    setupVisibilityToggle();
    setupImagePreview();
    setupItemSearch();
    setupUserSearch();
  });  