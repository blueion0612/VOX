package org.vox.capstonedesign1.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.vox.capstonedesign1.domain.Agent;
import org.vox.capstonedesign1.domain.AgentSignal;
import org.vox.capstonedesign1.domain.Device;
import org.vox.capstonedesign1.domain.EstimatedStatus;
import org.vox.capstonedesign1.dto.AgentSignalRequest;
import org.vox.capstonedesign1.repository.AgentRepository;
import org.vox.capstonedesign1.repository.AgentSignalRepository;
import org.vox.capstonedesign1.repository.DeviceRepository;
import org.vox.capstonedesign1.repository.EstimatedStatusRepository;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentSignalService {

    private final AgentSignalRepository agentSignalRepository;
    private final DeviceRepository deviceRepository;
    private final EstimatedStatusRepository estimatedStatusRepository;
    private final AgentRepository agentRepository;

    public void saveSignal(AgentSignalRequest request) {
        Agent agent = fetchAgentBySerialNumber(request);
        Device device = fetchDeviceBySerialNumber(request);
        EstimatedStatus estimatedStatus = fetchStatusById(request);
        LocalDateTime timeStamp = LocalDateTime.parse(request.getTimeStamp(), DateTimeFormatter.ISO_DATE_TIME);
        double streamingFrequency = request.getStreamingFrequency();
        AgentSignal agentSignal = AgentSignal.builder()
                .agent(agent)
                .device(device)
                .estimatedStatus(estimatedStatus)
                .timeStamp(timeStamp)
                .streamingFrequency(streamingFrequency)
                .build();
        agentSignalRepository.save(agentSignal);
    }

    private Agent fetchAgentBySerialNumber(AgentSignalRequest request) {
        String deviceSerialNumber = request.getDeviceSerialNumber();
        return agentRepository.findByDevice_DeviceSerialNumber(deviceSerialNumber)
                .orElseThrow(() -> new RuntimeException("디바이스 일련번호 " + deviceSerialNumber + "의 요원은 존재하지 않음"));
    }

    private Device fetchDeviceBySerialNumber(AgentSignalRequest request) {
        return deviceRepository.findByDeviceSerialNumber(request.getDeviceSerialNumber())
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 디바이스 일련번호"));
    }

    private EstimatedStatus fetchStatusById(AgentSignalRequest request) {
        return estimatedStatusRepository.findById(request.getStatusId())
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 상황 ID"));
    }
}
