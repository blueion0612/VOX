package org.vox.capstonedesign1.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.vox.capstonedesign1.domain.AgentSignal;

@Getter
@AllArgsConstructor
public class AgentSignalLogResponse {
    private String timeStamp;
    private String agentName;
    private String estimatedStatus;

    public AgentSignalLogResponse(AgentSignal signal) {
        this.timeStamp = signal.getTimeStamp().toString();
        this.agentName = signal.getAgent().getAgentName();
        this.estimatedStatus = signal.getEstimatedStatus().getStatusInformation();
    }
}
