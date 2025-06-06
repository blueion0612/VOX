const agentNames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"];
const agents = agentNames.map(name => ({ id: name, status: "Stable", lockedUntil: 0 }));


    const getRandomStatus = () => {
    const r = Math.random();
    if (r < 0.005) return "SOS";
    else if (r < 0.01) return "Need Connection";
    else if (r < 0.03) return "Need Support";
    else return "Stable";
    };

    function getStatusClass(status) {
        return `status-${status.replace(/ /g, '_')}`;
    }

    function createAgentElements() {
        const container = document.getElementById("agentsContainer");
        container.innerHTML = '';
        for (let agent of agents) {
        const wrapper = document.createElement('a');
        wrapper.href = "http://localhost:8080/";
        wrapper.className = "agent-link";

        const agentDiv = document.createElement('div');
        agentDiv.className = `agent ${getStatusClass(agent.status)}`;
        agentDiv.dataset.id = agent.id;

        const infoDiv = document.createElement('div');
        infoDiv.className = "info";

        infoDiv.innerHTML = `
            <div>${agent.id}</div>
            <div class="agent-status"><h1>${agent.status}</h1></div>
            <div><h5>Samsung s10</h5></div>
        `;

        const iframe = document.createElement('iframe');
        iframe.className = "smallunity-frame";
        iframe.src = "http://localhost:8080/";

        agentDiv.appendChild(infoDiv);
        agentDiv.appendChild(iframe);
        wrapper.appendChild(agentDiv);
        container.appendChild(wrapper);
        }
    }

    function updateAgentElements() {
        for (let agent of agents) {
        const agentDiv = document.querySelector(`.agent[data-id="${agent.id}"]`);
        if (agentDiv) {
            agentDiv.className = `agent ${getStatusClass(agent.status)}`;
            agentDiv.querySelector(".agent-status h1").textContent = agent.status;
        }
        }
    }

    function logStatusChange(agentId, status) {
        const log = document.getElementById("statusLog");
        const timestamp = new Date().toLocaleTimeString();
        const entry = `[${timestamp}] Agent ${agentId}: ${status}\n`;
        log.textContent += entry + "\n";
        log.scrollTop = log.scrollHeight;
    }

    function updateAgents() {
        const now = Date.now();
        for (let agent of agents) {
        if (agent.status === "SOS") continue;
        if (now < agent.lockedUntil) continue;

        const newStatus = getRandomStatus();
        if (newStatus !== agent.status && newStatus !== "Stable") {
            logStatusChange(agent.id, newStatus);
        }

        agent.status = newStatus;

        if (newStatus === "SOS") {
            agent.lockedUntil = Infinity;
        } else if (newStatus === "Need Connection" || newStatus === "Need Support") {
            agent.lockedUntil = now + 10000;
        } else {
            agent.lockedUntil = 0;
        }
        }

        updateAgentElements();
    }

    createAgentElements();
    updateAgents();
    setInterval(updateAgents, 1000);