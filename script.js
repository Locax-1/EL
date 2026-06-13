const authPage = document.querySelector("#authPage");
const calendarPage = document.querySelector("#calendarPage");
const historyPage = document.querySelector("#historyPage");

const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const authTip = document.querySelector("#authTip");
const registerBtn = document.querySelector("#registerBtn");
const loginBtn = document.querySelector("#loginBtn");

const monthTitle = document.querySelector("#monthTitle");
const calendarGrid = document.querySelector("#calendarGrid");
const prevMonthBtn = document.querySelector("#prevMonthBtn");
const nextMonthBtn = document.querySelector("#nextMonthBtn");

const recordPrompt = document.querySelector("#recordPrompt");
const addBtn = document.querySelector("#addBtn");
const recordList = document.querySelector("#recordList");

const aiAnalyzeBtn = document.querySelector("#aiAnalyzeBtn");

const historyBtn = document.querySelector("#historyBtn");
const userBtn = document.querySelector("#userBtn");
const historyYear = document.querySelector("#historyYear");
const monthList = document.querySelector("#monthList");
const backToCalendarBtn = document.querySelector("#backToCalendarBtn");

const entryModal = document.querySelector("#entryModal");
const typeInput = document.querySelector("#typeInput");
const amountInput = document.querySelector("#amountInput");
const cancelEntryBtn = document.querySelector("#cancelEntryBtn");
const saveEntryBtn = document.querySelector("#saveEntryBtn");

const logoutModal = document.querySelector("#logoutModal");
const cancelLogoutBtn = document.querySelector("#cancelLogoutBtn");
const confirmLogoutBtn = document.querySelector("#confirmLogoutBtn");

const weekNames = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];

const today = new Date();
let currentYear = today.getFullYear();
let currentMonth = today.getMonth(); // 0-11
let selectedDateKey = "";

function showPage(pageName) {
  authPage.classList.toggle("hidden", pageName !== "auth");
  calendarPage.classList.toggle("hidden", pageName !== "calendar");
  historyPage.classList.toggle("hidden", pageName !== "history");
}

function accountKey(username) {
  return `calendar-account-${username}`;
}

function getLoggedInUser() {
  return localStorage.getItem("calendar-current-user") || "";
}

function setLoggedInUser(username) {
  localStorage.setItem("calendar-current-user", username);
}

function getAccounts() {
  return JSON.parse(localStorage.getItem("calendar-accounts") || "{}");
}

function saveAccounts(accounts) {
  localStorage.setItem("calendar-accounts", JSON.stringify(accounts));
}

function showAuthTip(message) {
  authTip.textContent = message;
}

function register() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  if (!username || !password) {
    showAuthTip("账号和密码不能为空");
    return;
  }

  const accounts = getAccounts();
  if (accounts[username]) {
    showAuthTip("账号已存在，请直接登录");
    return;
  }

  accounts[username] = { password };
  saveAccounts(accounts);
  setLoggedInUser(username);
  showAuthTip("");
  enterCalendar(today.getFullYear(), today.getMonth());
}

function login() {
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();
  const accounts = getAccounts();

  if (!username || !password) {
    showAuthTip("账号和密码不能为空");
    return;
  }

  if (!accounts[username] || accounts[username].password !== password) {
    showAuthTip("账号或密码错误");
    return;
  }

  setLoggedInUser(username);
  showAuthTip("");
  enterCalendar(today.getFullYear(), today.getMonth());
}

function dateKey(year, month, day) {
  const m = String(month + 1).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  return `${year}-${m}-${d}`;
}

function recordsStorageKey() {
  const username = getLoggedInUser();
  return `calendar-records-${username}`;
}

function getAllRecords() {
  return JSON.parse(localStorage.getItem(recordsStorageKey()) || "{}");
}

function saveAllRecords(records) {
  localStorage.setItem(recordsStorageKey(), JSON.stringify(records));
}

function getRecords(key) {
  const all = getAllRecords();
  return all[key] || [];
}

function setRecords(key, list) {
  const all = getAllRecords();
  all[key] = list;
  saveAllRecords(all);
}

function enterCalendar(year, month) {
  currentYear = year;
  currentMonth = month;
  selectedDateKey = "";
  recordPrompt.textContent = "单击日期来记账";
  addBtn.classList.add("hidden");
  recordList.innerHTML = "";
  renderCalendar();
  showPage("calendar");
}

function renderCalendar() {
  calendarGrid.innerHTML = "";
  monthTitle.textContent = `${currentYear}年${currentMonth + 1}月`;

  weekNames.forEach((name) => {
    const cell = document.createElement("div");
    cell.className = "week-cell";
    cell.textContent = name;
    calendarGrid.appendChild(cell);
  });

  const firstDay = new Date(currentYear, currentMonth, 1).getDay();
  const totalDays = new Date(currentYear, currentMonth + 1, 0).getDate();

  for (let i = 0; i < firstDay; i += 1) {
    const empty = document.createElement("button");
    empty.className = "day-cell empty";
    empty.disabled = true;
    calendarGrid.appendChild(empty);
  }

  for (let day = 1; day <= totalDays; day += 1) {
    const btn = document.createElement("button");
    btn.className = "day-cell";
    btn.textContent = day;

    // 1号接近白色，最后一天渐变到正常粉色
    const ratio = totalDays === 1 ? 1 : (day - 1) / (totalDays - 1);
    const red = 255;
    const green = Math.round(250 - 68 * ratio);
    const blue = Math.round(250 - 58 * ratio);
    btn.style.backgroundColor = `rgb(${red}, ${green}, ${blue})`;

    const isToday =
      currentYear === today.getFullYear() &&
      currentMonth === today.getMonth() &&
      day === today.getDate();

    if (isToday) {
      btn.classList.add("today");
    }

    const key = dateKey(currentYear, currentMonth, day);
    if (key === selectedDateKey) {
      btn.classList.add("selected");
    }

    btn.addEventListener("click", () => selectDate(day));
    calendarGrid.appendChild(btn);
  }
}

function selectDate(day) {
  selectedDateKey = dateKey(currentYear, currentMonth, day);
  recordPrompt.textContent = "开始记账吧！";
  addBtn.classList.remove("hidden");
  renderCalendar();
  renderRecords();
}

function renderRecords() {
  recordList.innerHTML = "";

  if (!selectedDateKey) {
    return;
  }

  const records = getRecords(selectedDateKey);
  records.forEach((record, index) => {
    const row = document.createElement("div");
    row.className = "record-row";
    row.innerHTML = `
      <span>${index + 1}</span>
      <span>${escapeHtml(record.type)}</span>
      <span>${escapeHtml(record.amount)}</span>
    `;
    recordList.appendChild(row);
  });
}

function openEntryModal() {
  if (!selectedDateKey) return;
  typeInput.value = "";
  amountInput.value = "";
  entryModal.classList.remove("hidden");
  typeInput.focus();
}

function closeEntryModal() {
  entryModal.classList.add("hidden");
}

function saveEntry() {
  const type = typeInput.value.trim();
  const amount = amountInput.value.trim();

  if (!type || !amount) {
    alert("输入不足，保存失败");
    return;
  }

  const records = getRecords(selectedDateKey);
  records.push({ type, amount });
  setRecords(selectedDateKey, records);
  closeEntryModal();
  recordPrompt.textContent = "开始记账吧！";
  renderRecords();
}

function renderHistory() {
  const year = today.getFullYear();
  const startMonth = today.getMonth();

  historyYear.textContent = `${year}年`;
  monthList.innerHTML = "";

  for (let month = startMonth; month >= 0; month -= 1) {
    const btn = document.createElement("button");
    btn.className = "month-item";
    btn.textContent = `${month + 1}月`;
    btn.addEventListener("click", () => enterCalendar(year, month));
    monthList.appendChild(btn);
  }

  showPage("history");
}

function openLogoutModal() {
  logoutModal.classList.remove("hidden");
}

function closeLogoutModal() {
  logoutModal.classList.add("hidden");
}

function logout() {
  localStorage.removeItem("calendar-current-user");
  closeLogoutModal();
  usernameInput.value = "";
  passwordInput.value = "";
  showAuthTip("");
  showPage("auth");
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (match) => {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return map[match];
  });
}

registerBtn.addEventListener("click", register);
loginBtn.addEventListener("click", login);

prevMonthBtn.addEventListener("click", () => {
  const target = new Date(currentYear, currentMonth - 1, 1);
  enterCalendar(target.getFullYear(), target.getMonth());
});

nextMonthBtn.addEventListener("click", () => {
  const target = new Date(currentYear, currentMonth + 1, 1);
  enterCalendar(target.getFullYear(), target.getMonth());
});

addBtn.addEventListener("click", openEntryModal);
cancelEntryBtn.addEventListener("click", closeEntryModal);
saveEntryBtn.addEventListener("click", saveEntry);

historyBtn.addEventListener("click", renderHistory);
backToCalendarBtn.addEventListener("click", () => enterCalendar(currentYear, currentMonth));

userBtn.addEventListener("click", openLogoutModal);
cancelLogoutBtn.addEventListener("click", closeLogoutModal);
confirmLogoutBtn.addEventListener("click", logout);

// 刷新页面时：如果已经登录，就直接进入当前月份；否则显示登录页
if (getLoggedInUser()) {
  enterCalendar(today.getFullYear(), today.getMonth());
} else {
  showPage("auth");
}

