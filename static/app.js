document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) window.lucide.createIcons();
  const toggle = document.getElementById("menu-toggle");
  const navigation = document.getElementById("navigation");
  if (toggle && navigation) {
    toggle.addEventListener("click", () => {
      const expanded = navigation.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(expanded));
    });
  }
  const data = document.getElementById("product-data");
  if (data) {
    const products = JSON.parse(data.textContent);
    const select = document.getElementById("id_product");
    const packages = document.getElementById("id_packages");
    const content = document.getElementById("id_content");
    const total = document.getElementById("receipt-total");
    const selected = () => products.find(product => String(product.id) === select.value);
    const update = () => {
      const product = selected();
      const quantity = Number(packages.value) * Number(content.value);
      total.textContent = product && Number.isFinite(quantity) && quantity > 0
        ? `Total: ${quantity.toLocaleString("es-MX", {maximumFractionDigits: 3})} ${product.unit}` : "";
    };
    select.addEventListener("change", () => {
      const product = selected();
      if (product) content.value = product.package_size;
      update();
    });
    packages.addEventListener("input", update);
    content.addEventListener("input", update);
    update();
  }
});