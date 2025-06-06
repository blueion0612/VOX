const params = new URLSearchParams(window.location.search);
const name = params.get("name");
const status = params.get("status");

document.getElementById("agentName").textContent = name || "Agent";
document.getElementById("agentStatus").textContent = status || "Status Unknown";
