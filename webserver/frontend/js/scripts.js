const statuses = ["SOS", "Stable", "Need Support", "Need Connection"];

function getStatusClass(status) {
    return `status-${status.replace(/ /g, '_')}`;  
}


function getAgentHTML(id, status) {
return `
    <a href="http://192.168.45.190:8006/" class="agent-link">
    <div class="agent ${getStatusClass(status)}">
        <div class="info">
        <div>Agent ${id}</div>
        <div class="agent-status"><h1>${status}</h1></div>
        <div><h5>Samsung s10</h5></div>
        </div>
        <img class="smallunity" src="https://i.ibb.co/8Dzrdzsc/image.png" alt="robot">
    </div>
    </a>
`;
}

function updateAgents() {
const container = document.getElementById("agentsContainer");
container.innerHTML = "";
for (let i = 1; i <= 9; i++) {
    const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
    container.innerHTML += getAgentHTML(i, randomStatus);
}
}

updateAgents();
setInterval(updateAgents, 1000);
