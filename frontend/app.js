const API_URL = "https://order-manager-cloud.onrender.com/api/orders";

const state = { orders: [], deletingId: null };
const $ = (selector) => document.querySelector(selector);
const elements = {
  body: $("#orders-body"), empty: $("#empty-state"), resultCount: $("#result-count"),
  totalRevenue: $("#total-revenue"), totalOrders: $("#total-orders"),
  processingOrders: $("#processing-orders"), completedOrders: $("#completed-orders"),
  search: $("#search-input"), filter: $("#status-filter"), modal: $("#order-modal"),
  deleteModal: $("#delete-modal"), form: $("#order-form"), formError: $("#form-error"),
  save: $("#save-button"), toast: $("#toast")
};

const currency = new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 });
const escapeHtml = (text = "") => String(text).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
const statusClass = (status) => ({ "Mới": "badge-new", "Đang xử lý": "badge-processing", "Hoàn thành": "badge-completed" })[status];

async function api(path = "", options = {}) {
  const response = await fetch(`${API_URL}${path}`, { headers: { "Content-Type": "application/json", ...options.headers }, ...options });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
    throw new Error(detail || "Không thể kết nối tới máy chủ");
  }
  return response.status === 204 ? null : response.json();
}

async function loadData() {
  try {
    const [orders, summary] = await Promise.all([api(), api("/summary")]);
    state.orders = orders;
    elements.totalRevenue.textContent = currency.format(summary.total_revenue);
    elements.totalOrders.textContent = summary.total_orders;
    elements.processingOrders.textContent = summary.processing_orders;
    elements.completedOrders.textContent = summary.completed_orders;
    renderOrders();
  } catch (error) {
    showToast(error.message, true);
    elements.resultCount.textContent = "Không thể tải dữ liệu";
  }
}

function renderOrders() {
  const query = elements.search.value.trim().toLocaleLowerCase("vi");
  const status = elements.filter.value;
  const orders = state.orders.filter((order) => {
    const searchable = `${order.customer_name} ${order.product_name} ${order.id}`.toLocaleLowerCase("vi");
    return (!query || searchable.includes(query)) && (!status || order.status === status);
  });
  elements.resultCount.textContent = `${orders.length} đơn hàng${orders.length !== state.orders.length ? ` trên tổng số ${state.orders.length}` : ""}`;
  elements.empty.hidden = orders.length > 0;
  elements.body.innerHTML = orders.map((order) => `
    <tr>
      <td><span class="order-id">#${String(order.id).padStart(4, "0")}</span></td>
      <td><span class="customer">${escapeHtml(order.customer_name)}</span></td>
      <td>${escapeHtml(order.product_name)}${order.note ? `<small class="product-note" title="${escapeHtml(order.note)}">${escapeHtml(order.note)}</small>` : ""}</td>
      <td>${order.quantity}</td>
      <td><span class="money">${currency.format(order.total)}</span></td>
      <td><span class="badge ${statusClass(order.status)}">${order.status}</span></td>
      <td><div class="row-actions"><button class="icon-button edit" data-id="${order.id}" aria-label="Sửa đơn hàng" title="Sửa">✎</button><button class="icon-button delete" data-id="${order.id}" aria-label="Xóa đơn hàng" title="Xóa">×</button></div></td>
    </tr>`).join("");
}

function openForm(order = null) {
  elements.form.reset();
  elements.formError.textContent = "";
  $("#order-id").value = order?.id || "";
  $("#customer-name").value = order?.customer_name || "";
  $("#product-name").value = order?.product_name || "";
  $("#quantity").value = order?.quantity || 1;
  $("#unit-price").value = order?.unit_price ?? "";
  $("#status").value = order?.status || "Mới";
  $("#note").value = order?.note || "";
  $("#modal-title").textContent = order ? "Cập nhật đơn hàng" : "Thêm đơn hàng";
  elements.save.textContent = order ? "Lưu thay đổi" : "Tạo đơn hàng";
  elements.modal.hidden = false;
  document.body.style.overflow = "hidden";
  setTimeout(() => $("#customer-name").focus(), 50);
}

function closeModals() {
  elements.modal.hidden = true;
  elements.deleteModal.hidden = true;
  document.body.style.overflow = "";
}

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.className = `toast show${isError ? " error" : ""}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => elements.toast.className = "toast", 2800);
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = $("#order-id").value;
  const payload = { customer_name: $("#customer-name").value, product_name: $("#product-name").value, quantity: Number($("#quantity").value), unit_price: Number($("#unit-price").value), status: $("#status").value, note: $("#note").value };
  elements.save.disabled = true;
  elements.formError.textContent = "";
  try {
    await api(id ? `/${id}` : "", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) });
    closeModals();
    showToast(id ? "Đã cập nhật đơn hàng" : "Đã thêm đơn hàng mới");
    await loadData();
  } catch (error) { elements.formError.textContent = error.message; }
  finally { elements.save.disabled = false; }
});

elements.body.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-id]");
  if (!button) return;
  const order = state.orders.find((item) => item.id === Number(button.dataset.id));
  if (button.classList.contains("edit")) openForm(order);
  if (button.classList.contains("delete")) { state.deletingId = order.id; elements.deleteModal.hidden = false; document.body.style.overflow = "hidden"; }
});

$("#confirm-delete").addEventListener("click", async () => {
  const button = $("#confirm-delete"); button.disabled = true;
  try { await api(`/${state.deletingId}`, { method: "DELETE" }); closeModals(); showToast("Đã xóa đơn hàng"); await loadData(); }
  catch (error) { showToast(error.message, true); }
  finally { button.disabled = false; state.deletingId = null; }
});

$("#add-order-button").addEventListener("click", () => openForm());
$("#close-modal").addEventListener("click", closeModals);
$("#cancel-button").addEventListener("click", closeModals);
$("#cancel-delete").addEventListener("click", closeModals);
elements.search.addEventListener("input", renderOrders);
elements.filter.addEventListener("change", renderOrders);
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeModals(); });
[elements.modal, elements.deleteModal].forEach((modal) => modal.addEventListener("click", (event) => { if (event.target === modal) closeModals(); }));

loadData();
