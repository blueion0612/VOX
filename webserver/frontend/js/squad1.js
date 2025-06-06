const agents = Array.from({ length: 9 }, (_, i) => ({ id: i + 1, status: "Stable", lockedUntil: 0 }));

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

    function getAgentHTML(agent) {
    return `
        <a href="http://192.168.45.190:8006/" class="agent-link">
        <div class="agent ${getStatusClass(agent.status)}">
            <div class="info">
            <div>Agent ${agent.id}</div>
            <div class="agent-status"><h1>${agent.status}</h1></div>
            <div><h5>Samsung s10</h5></div>
            </div>
            <img class="smallunity" src="https://i.ibb.co/8Dzrdzsc/image.png" alt="robot">
        </div>
        </a>
    `;
    }
    
    // function getAgentHTML(agent) {
    // return `
    //     <a href="http://192.168.45.190:8006/" class="agent-link">
    //     <div class="agent ${getStatusClass(agent.status)}">
    //         <div class="info">
    //         <div>Agent ${agent.id}</div>
    //         <div class="agent-status"><h1>${agent.status}</h1></div>
    //         <div><h5>Samsung s10</h5></div>
    //         </div>
    //         <iframe class="smallunity-frame" src="http://192.168.45.190:8006/"></iframe>
    //     </div>
    //     </a>
    // `;
    // }

    function logStatusChange(agentId, status) {
    const log = document.getElementById("statusLog");
    const timestamp = new Date().toLocaleTimeString();
    const entry = `[${timestamp}] Agent ${agentId}: ${status}\n`;
    log.textContent += entry;
    log.textContent += "\n";
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
        agent.lockedUntil = now + 5000;
        } else {
        agent.lockedUntil = 0;
        }
    }

    const container = document.getElementById("agentsContainer");
    container.innerHTML = agents.map(getAgentHTML).join('');
    }

    updateAgents();
    setInterval(updateAgents, 1000);